import datetime
from dataclasses import dataclass, field

import docs
import memberdata
import keys

# TODO: add some type of handling of multiple attestations for same household

@dataclass
class AccountAttest:
    account_num: str
    web_view_links: list[str] = field(default_factory=lambda: [])
    people: list[docs.AttestEntry] = field(default_factory=lambda: [])

account_attest_map: dict[str,AccountAttest] = {}

def record_attestation(membership: memberdata.Membership, attestation: docs.Attestation) -> None:
    primary_name = attestation.adults[0].name
    account = membership.get_account_by_fullname(primary_name)
    if account is None:
        print(f"Failed to find account for {primary_name}")
        print(f"doc: {attestation.web_view_link}")
        return
    
    account_attest = account_attest_map.get(account.account_num)
    if account_attest is None:
        account_attest = AccountAttest(account.account_num)
        account_attest_map[account.account_num] = account_attest

    account_attest.web_view_links.append(attestation.web_view_link)
    for entry in attestation.adults:
        account_attest.people.append(entry)
    for entry in attestation.minors:
        account_attest.people.append(entry)


reported: dict[str,bool] = {}
def report_once(account: memberdata.AccountEntry):
    if account.account_num in reported:
        return

    reported[account.account_num] = True
    print(f"Account: {account.account_num} {account.billing_name} - {account.account_type}")
    account_attest = account_attest_map.get(account.account_num)
    if account_attest is not None:
        for web_link in account_attest.web_view_links:
            print(f"\t{web_link}")

# check caretaker type
# add info on web links
# print count of accounts
def review_account(membership: memberdata.Membership, member_keys: keys.MemberKeys, account: memberdata.AccountEntry):
    # Get Attestation for the account
    account_attest: AccountAttest | None = account_attest_map.get(account.account_num)
    if account_attest is None:
       return
    reported = False

    known_members = membership.get_members_for_account_num(account.account_num)
    attested_members = set()

    for attest_entry in account_attest.people:
        name = memberdata.MemberName.CreateMemberName(attest_entry.name)
        if name is None:
            report_once(account)
            print(f"\tError: unable to parse name {attest_entry.name}")
            reported = True
            continue

        members = membership.find_members_by_name(name)
        if len(members) == 0:
            report_once(account)
            print(f"\tError: unable to find name {attest_entry.name}")
            reported = True
            continue

        attested_members.add(members[0])

    # Check all members are attested
    for member in known_members:
        if not member in attested_members:
            if not member.is_caretaker_type():
                report_once(account)
                reported = True
                key_status = "no key"
                if member_keys.has_key(member.member_id):
                    key_status = "has key"
                if member_keys.has_enabled_key(member.member_id):
                    key_status = "has enabled key"
                print(f"\tMember {member.name.fullname()} is not attested. Key status: {key_status}")

    # Check if attestation have emails when memberdata does not and check
    # if birthdays differ
    if (reported):
        print("")
    # TODO

def main():
    attestations = docs.Attestation.read_csv()
    membership = memberdata.Membership()
    membership.read_csv_files()

    member_keys = keys.MemberKeys()
    member_keys.load_keys(membership)

    for attestation in attestations:
        record_attestation(membership, attestation)

    for account in membership.accounts():
        if not account.account_num in account_attest_map:
            report_once(account)
            print(f"\tError: no attestation for account {account.account_num}")
            key_status = False
            for member in membership.get_members_for_account_num(account.account_num):
                if member_keys.has_key(member.member_id):
                    key_status = True
            if key_status:
                print(f"\tBut account has an electronic key issued")


    for account in membership.accounts():
        review_account(membership, member_keys, account)


if __name__ == "__main__":
    main()
