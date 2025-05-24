"""
Generate list of members that are covered by a signed waiver

Input:
- membership data
- attestations.csv
- member_waivers.csv

Output:
- waivered_members.csv
"""

from dataclasses import dataclass
import csv

import docs
import csvfile
import memberdata

waiver_out_filename = "output/waivered_members.csv"


@dataclass
class WaiveredMember:
    """Represents an member covered by a waiver"""

    member: memberdata.MemberEntry
    doc_link: str
    waiver_signed: bool

    FIELD_ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    FIELD_MEMBER_ID = csvfile.MEMBER_ID
    FIELD_FIRST_NAME = "First Name"
    FIELD_LAST_NAME = "Last Name"
    FIELD_MEMBER_TYPE = "Type"
    FIELD_WAIVER_SIGNED = "Signed"
    FIELD_DOC_LINK = "Doc Link"

    @staticmethod
    def get_header():
        return [
            WaiveredMember.FIELD_ACCOUNT_NUM,
            WaiveredMember.FIELD_MEMBER_ID,
            WaiveredMember.FIELD_FIRST_NAME,
            WaiveredMember.FIELD_LAST_NAME,
            WaiveredMember.FIELD_MEMBER_TYPE,
            WaiveredMember.FIELD_WAIVER_SIGNED,
            WaiveredMember.FIELD_DOC_LINK,
        ]

    def get_row(self) -> dict[str, str]:
        row = {
            WaiveredMember.FIELD_ACCOUNT_NUM: self.member.account_num,
            WaiveredMember.FIELD_MEMBER_ID: self.member.member_id,
            WaiveredMember.FIELD_FIRST_NAME: self.member.name.first_name,
            WaiveredMember.FIELD_LAST_NAME: self.member.name.last_name,
            WaiveredMember.FIELD_MEMBER_TYPE: self.member.member_type,
            WaiveredMember.FIELD_WAIVER_SIGNED: "YES",
            WaiveredMember.FIELD_DOC_LINK: self.doc_link,
        }
        return row


def check_waiver(
    membership: memberdata.Membership, waiver: docs.MemberWaiver
) -> bool:
    """
    Return True if waiver is considered to be complete.
    All required signatures and minors are included for a family waiver.
    A complete family waiver means that all minors and all signers are covered
    TODO: check that both parents have signed
    """

    if len(waiver.signatures) < 1:
        return False

    if waiver.type == docs.MemberWaiver.TYPE_INDIVIDUAL:
        return True

    name = waiver.signatures[0].name
    account = membership.get_account_by_fullname(name)
    if account is None:
        print(f"Warning: no account for name '{name}'")
        return False

    # Count number of minor children
    minors = 0
    for member in membership.get_members_for_account_num(account.account_num):
        if member.is_minor():
            minors += 1

    return minors == 0 or minors <= len(waiver.minors)


def main() -> None:
    membership = memberdata.Membership()
    membership.read_csv_files()
    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()

    waivers: list[WaiveredMember] = []

    # Set of member ids
    covered_member_ids: set[str] = set()

    # Scan attestations
    for entry in attestations:
        signing_name = entry.adults[0].name
        signing_email = entry.adults[0].email
        members = membership.get_members_by_fullname(signing_name)
        if len(members) != 1:
            # Find member with matching email
            members = list(filter(lambda x: x.email == signing_email, members))

        if len(members) != 1:
            print(
                f"Error: unable to determine signer '{signing_name}' in doc {entry.web_view_link}"
            )
            continue

        if members[0].member_id not in covered_member_ids:
            covered_member_ids.add(members[0].member_id)
            waivers.append(WaiveredMember(members[0], entry.web_view_link, True))

    # Scan member waivers
    for member_waiver in member_waivers:
        for signature in member_waiver.signatures:
            members = membership.get_members_by_fullname(signature.name)
            if len(members) != 1:
                print(
                    f"Error: unable to determine signer '{signature.name}' in doc {member_waiver.web_view_link} ({len(members)})"
                )
            else:
                if members[0].member_id not in covered_member_ids:
                    covered_member_ids.add(members[0].member_id)
                    waivers.append(
                        WaiveredMember(members[0], member_waiver.web_view_link, True)
                    )

        if member_waiver.complete:
            for minor in member_waiver.minors:
                members = membership.get_members_by_fullname(minor)
                if len(members) != 1:
                    print(
                        f"Error: unable to determine minor '{minor}' in doc {member_waiver.web_view_link}"
                    )
                else:
                    if members[0].member_id not in covered_member_ids:
                        covered_member_ids.add(members[0].member_id)
                        waivers.append(
                            WaiveredMember(
                                members[0], member_waiver.web_view_link, True
                            )
                        )

    output_file = open(waiver_out_filename, "w", newline="")
    output_csv = csv.DictWriter(output_file, fieldnames=WaiveredMember.get_header())
    output_csv.writeheader()

    for waiver in waivers:
        output_csv.writerow(waiver.get_row())
    output_file.close()
    print(f"Note: created {waiver_out_filename}")


if __name__ == "__main__":
    main()
