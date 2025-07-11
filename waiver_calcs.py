"""
Logic to support waiver operations
- complete
- signed
- update waiver records

Todo: Generate list of members that are covered by a signed waiver
"""

from __future__ import annotations
import sys

from dataclasses import dataclass
import csv

import docs
import csvfile
import memberdata
import waiverrec
import keys

waivered_member_filename = "output/waivered_members.csv"


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
    def read_row(membership: memberdata.Membership,
                 row: dict[str,str]) -> WaiveredMember|None:
        member_id = row[WaiveredMember.FIELD_MEMBER_ID]
        doc_link = row[WaiveredMember.FIELD_DOC_LINK]
        waiver_signed = csvfile.is_signed(row[WaiveredMember.FIELD_WAIVER_SIGNED])
        member_entry = membership.get_member_by_id(member_id)
        if member_entry is not None:
            return WaiveredMember(member_entry, doc_link, waiver_signed)
        return None

    @staticmethod
    def read_csv(membership: memberdata.Membership, filename: str = waivered_member_filename) -> list[WaiveredMember]:
        print(f"Note: reading {filename}")
        result: list[WaiveredMember] = []
        with open(filename, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                member = WaiveredMember.read_row(membership, row)
                if not member is None:
                    result.append(member)
                else:
                    print(f"Warning: member {row[WaiveredMember.FIELD_MEMBER_ID]} not found")
        return result


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

def gen_waivered_member_list(membership: memberdata.Membership, 
                             groups: waiverrec.MemberWaiverGroups,
                             attestations: list[docs.Attestation],
                             waiver_docs: list[docs.MemberWaiver]) -> None:
    """
    Generate list of all members covered by a waiver using the waiver records.
    TODO: not all waiver info is in the waivered groups. 
    - adults with minor children that  signed a member waiver or incomplete family waiver
    - adults with minor children that signed an attestation
    """

    waivers: list[WaiveredMember] = []

    # Set of member ids
    covered_member_ids: set[str] = set()

    # Scan family waiver recs
    for family_record in groups.with_minor_children:
        if not family_record.signed:
            continue
        for adult in family_record.adults:
            if adult.member_id not in covered_member_ids:
                covered_member_ids.add(adult.member_id)
                waivers.append(WaiveredMember(adult, family_record.web_link, waiver_signed=True))
        for minor in family_record.minors:
            if minor.member_id not in covered_member_ids:
                covered_member_ids.add(minor.member_id)
                waivers.append(WaiveredMember(minor, family_record.web_link, waiver_signed=True))

    # Scan member adult waiver recs
    for adult_record in groups.no_minor_children:
        if adult_record.signed and adult_record.member.member_id not in covered_member_ids:
            covered_member_ids.add(adult_record.member.member_id)
            waivers.append(WaiveredMember(adult_record.member, adult_record.web_link, waiver_signed=True))

    # Adults with minor children may be covered by an attestation, individual member waiver, or incomplete family waiver
    for attest in attestations:
        if len(attest.adults) < 1:
            continue
        name = attest.adults[0].name        
        member = membership.get_one_member_by_fullname(name, minor=False)
        if member is None:
            if not attest.is_reviewed():
                print(f"No result for {name} from {attest.web_view_link}")
            continue
        if not member.member_id in covered_member_ids:
            covered_member_ids.add(member.member_id)
            waivers.append(WaiveredMember(member, attest.web_view_link, waiver_signed=True))

    for waiver_doc in waiver_docs:
        for signature in waiver_doc.signatures:
            name = signature.name
            member = membership.get_one_member_by_fullname(name, minor=False)
            if member is None:
                if not waiver_doc.is_reviewed():
                    print(f"No result for {name} from {waiver_doc.web_view_link}")
                continue
            if not member.member_id in covered_member_ids:
                covered_member_ids.add(member.member_id)
                waivers.append(WaiveredMember(member, waiver_doc.web_view_link, waiver_signed=True))

    output_file = open(waivered_member_filename, "w", newline="")
    output_csv = csv.DictWriter(output_file, fieldnames=WaiveredMember.get_header())
    output_csv.writeheader()

    for waiver in waivers:
        output_csv.writerow(waiver.get_row())
    output_file.close()
    print(f"Note: created {waivered_member_filename}")






def check_waiver(
    membership: memberdata.Membership, groups: waiverrec.MemberWaiverGroups, waiver: docs.MemberWaiver
) -> bool:
    """
    Return True if waiver is considered to be complete.
    All required signatures and minors are included for a family waiver.
    A complete family waiver means that all minors and all signers are covered
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
        # This happens if the family no longer has minor children
        # print(f"Warning: family waiver record not found for {name}")
        return True

    if len(family_record.adults) > len(waiver.signatures):
        return False

    return len(family_record.minors) <= len(waiver.minors)


def update_waiver_complete(membership: memberdata.Membership, waiver_groups: waiverrec.MemberWaiverGroups, waiver_docs: list[docs.MemberWaiver]) -> None:
    # Update complete state of family waivers
    for waiver_doc in waiver_docs:
        complete = check_waiver(membership, waiver_groups, waiver_doc)
        waiver_doc.set_complete(complete)

def review_member_waiver_docs(membership: memberdata.Membership, waiver_docs: list[docs.MemberWaiver]) -> None:
    print("Reviewing member waiver documents")
    for waiver_doc in waiver_docs:
        account_num = ''
        for signature in waiver_doc.signatures:
            member = membership.get_one_member_by_fullname(signature.name, False)
            if member is None:
                if not waiver_doc.is_reviewed():
                    print(f"Warning: No member found for signature {signature.name} in {waiver_doc.web_view_link}")
                continue
            if account_num == '':
                account_num = member.account_num 
            if account_num != member.account_num:
                print(f"Error: signatures from different accounts {signature.name}")


def update_waiver_status(membership: memberdata.Membership|None = None) -> None:
    print("Note: updating waiver records status")
    if membership is None:
        membership = memberdata.Membership()
        membership.read_csv_files()

    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()
    waiver_groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)

    update_waiver_complete(membership, waiver_groups, member_waivers)
    review_member_waiver_docs(membership, member_waivers)
    waiver_doc_map = docs.MemberWaiver.create_doc_map(member_waivers)
    # Also add lower case
    names = list(waiver_doc_map.keys())
    for name in names:
        waiver_doc_map[name.lower()] = waiver_doc_map[name]

    attest_doc_map = docs.Attestation.create_doc_map(attestations)
    names = list(attest_doc_map.keys())
    for name in names:
        attest_doc_map[name.lower()] = attest_doc_map[name]

    # Update the signed state of waviers 
    for adult_record in waiver_groups.no_minor_children:
        adult_record.signed = False
        name = adult_record.member.name.fullname().lower()

        waiver_doc = waiver_doc_map.get(name)
        if waiver_doc is not None:
            adult_record.web_link = waiver_doc.web_view_link
            adult_record.signed = waiver_doc.is_complete()
            continue

        attest_doc = attest_doc_map.get(name)
        if attest_doc is not None:
            adult_record.web_link = attest_doc.web_view_link
            adult_record.signed = True

    # Update signed state of family waivers
    for family_record in waiver_groups.with_minor_children:
        name = family_record.adults[0].name.fullname().lower()
        waiver_doc = waiver_doc_map.get(name)

        # Ensure this is a family waiver
        if waiver_doc is not None and waiver_doc.type == docs.MemberWaiver.TYPE_FAMILY:
            family_record.signed = waiver_doc.is_complete()
            family_record.web_link = waiver_doc.web_view_link
            # If not fully signed, look to the attest doc
            if family_record.signed:
                continue

        # Single parent signers of attestation
        if len(family_record.adults) == 1:
            attest_doc = attest_doc_map.get(name)
            if attest_doc is None:
                continue
            # Are all of the minors covered?
            if len(attest_doc.minors) >= len(family_record.minors):
                family_record.signed = True
                family_record.web_link = attest_doc.web_view_link

    member_records: list[waiverrec.MemberRecord] = []
    member_keys = keys.gen_member_key_map(membership)
    member_records = waiverrec.MemberRecord.gen_records(waiver_groups, member_keys)
    waiverrec.MemberRecord.write_csv(member_records, waiverrec.MemberRecord.member_csv)

    waiverrec.MemberWaiverGroups.write_csv_files(waiver_groups)
    docs.MemberWaiver.write_csv(member_waivers)
    gen_waivered_member_list(membership, waiver_groups, attestations, member_waivers)


def report_waiver_stats() -> None:
    membership = memberdata.Membership()
    membership.read_csv_files()

    member_waivers = docs.MemberWaiver.read_csv()
    waiver_groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)
    member_keys = keys.gen_member_key_map(membership)
    waivered_members = WaiveredMember.read_csv(membership)

    waivered_adult_count: int = 0
    unwaivered_adult_count: int = 0
    unwaivered_adult_with_keys_count: int = 0
    waivered_family_count: int = 0
    waivered_family_members: int = 0
    unwaivered_family_count: int = 0
    unwaivered_family_with_keys_count: int = 0
    unwaivered_family_members: int = 0
    
    total_adults = 0
    waivered_adults = 0
    total_minors = 0
    waivered_minors = 0
    total_members = 0
    for member in membership.all_members():
        if member.is_minor():
            total_minors += 1
        else:
            total_adults += 1
        total_members += 1

    for waivered_member in waivered_members:
        if waivered_member.member.is_minor():
            waivered_minors += 1
        else:
            waivered_adults += 1


    # Count varius records
    for adult_record in waiver_groups.no_minor_children:
        if adult_record.signed:
            waivered_adult_count += 1
        else:
            unwaivered_adult_count += 1
            if adult_record.member.member_id in member_keys:
                unwaivered_adult_with_keys_count += 1

    # Update signed state of family waivers
    for family_record in waiver_groups.with_minor_children:
        if family_record.signed:
            waivered_family_count += 1
            waivered_family_members += (len(family_record.adults) + len(family_record.minors))
        else:
            unwaivered_family_count += 1
            unwaivered_family_members += (len(family_record.adults) + len(family_record.minors))
            has_key = False
            for adult in family_record.adults:
                if adult.member_id in member_keys:
                    has_key = True
            for minor in family_record.minors:
                if minor.member_id in member_keys:
                    has_key = True
            if has_key:
                unwaivered_family_with_keys_count += 1

    total_keys = len(member_keys)
    enabled_keys = 0
    for key_entry in member_keys.values():
        if key_entry.enabled:
            enabled_keys += 1

    print()
    print("Stats - Progress")
    print(f"Member waiver docs: {len(member_waivers)}")
    print(f"Adults waivers: {waivered_adult_count} signed, {unwaivered_adult_count} unsigned")
    print(f"Adults with keys no waiver: {unwaivered_adult_with_keys_count}")
    print(f"Family waivers signed: {waivered_family_members} members in {waivered_family_count} families")
    print(f"Family waivers unsigned: {unwaivered_family_members} members in {unwaivered_family_count} families, {unwaivered_family_with_keys_count} with keys")
    print()
    print("Note: these stats report progress on needed signatures. Does not report all adults covered by waivers")
    print()
    print("Totals:")
    print(f"Adults:  {waivered_adults} waivered / {total_adults} total")
    print(f"Minors: {waivered_minors} waivered / {total_minors} total")
    print(f"Members: {total_members} total")
    print(f"Members allocated keys: {enabled_keys} enabled / {total_keys} total")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1].lower() == "update":
        update_waiver_status()
    elif len(sys.argv) > 1:
        print("Usage: {sys.argv[0]} [ update ]")
        sys.exit(-1)

    report_waiver_stats()

if __name__ == "__main__":
    main()
