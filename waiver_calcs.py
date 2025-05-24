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
import waiverrec

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
    membership: memberdata.Membership, groups: waiverrec.MemberWaiverGroups, waiver: docs.MemberWaiver
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

    family_record = groups.find_family_record(name)
    if family_record is None:
        print(f"Warning: family waiver record not found for {name}")
        return False

    if len(family_record.adults) > len(waiver.signatures):
        return False

    return len(family_record.minors) <= len(waiver.minors)


def update_waiver_complete(membership: memberdata.Membership, waiver_groups: waiverrec.MemberWaiverGroups, waiver_docs: list[docs.MemberWaiver]) -> None:
    # Update complete state of family waivers
    for waiver_doc in waiver_docs:
        waiver_doc.set_complete(check_waiver(membership, waiver_groups, waiver_doc))


def update_waiver_status() -> None:
    pass
    membership = memberdata.Membership()
    membership.read_csv_files()

    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()
    waiver_groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)

    update_waiver_complete(membership, waiver_groups, member_waivers)
    waiver_doc_map = docs.MemberWaiver.create_doc_map(member_waivers)
    attest_doc_map = docs.Attestation.create_doc_map(attestations)

    # Update the signed state of waviers 
    for adult_record in waiver_groups.no_minor_children:
        adult_record.signed = False
        name = adult_record.member.name.fullname()

        waiver_doc = waiver_doc_map.get(name)
        if waiver_doc is not None:
            adult_record.signed = csvfile.is_signed(waiver_doc.complete)
            continue

        attest_doc = attest_doc_map.get(name)
        if attest_doc is not None:
            adult_record.signed = True

    # Update signed state of family waivers
    for family_record in waiver_groups.with_minor_children:
        name = family_record.adults[0].name.fullname()
        waiver_doc = waiver_doc_map.get(name)
        if waiver_doc is None:
            continue
        family_record.signed = csvfile.is_signed(waiver_doc.complete)

    
    waiverrec.MemberWaiverGroups.write_csv_files(waiver_groups)





def main() -> None:
    update_waiver_status()

if __name__ == "__main__":
    main()
