import datetime

import attest
import memberdata

# TODO: add some type of handling of multiple attestations for same household

def review_attestation(membership, attestation):
    # Get account matching attestation
    primary_name = attestation.adults[0].name
    account = membership.get_account_by_fullname(primary_name)
    if account is None:
        print(f"Failed to find account for {primary_name}")
        return
    print(f"Found account {account.account_num} for {primary_name}")
    print(attestation.web_view_link)

    members = membership.get_members_for_account_num(account.account_num)
    member_names = [member.name.fullname().lower() for member in members]

    attest_entries = {entry.name.lower(): entry for entry in attestation.adults}
    attest_entries.update({entry.name.lower(): entry for entry in attestation.minors})

    # Check all entries are members
    for entry in attest_entries.values():
        if entry.name.lower() not in member_names:
            print(f"\tAttested name is not a member: {entry.name}")

    # Check all members are attested
    for member in members:
        if member.name.fullname().lower() not in attest_entries:
            print(f"\tMember {member.name.fullname()} is not attested")

    # Check if attestation have emails when memberdata does not and check
    # if birthdays differ
    for member in members:
        if (entry := attest_entries.get(member.name.fullname().lower())) is not None:
            if len(member.email) == 0 and len(entry.email) > 0:
                print(f"\tEmail for {member.name} available: {entry.email}")
            if (
                member.birthdate == datetime.date.min
                and entry.birthdate != datetime.date.min
            ):
                print(f"\tBrithday for {member.name} available: {entry.birthdate}")


def main():
    attestations = attest.read_attestations_csv()
    membership = memberdata.Membership()
    membership.read_csv_files()

    for attestation in attestations:
        review_attestation(membership, attestation)


if __name__ == "__main__":
    main()
