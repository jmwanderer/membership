"""
Logic to support waiver operations
- complete
- signed
- update waiver records

Todo: Generate list of members that are covered by a signed waiver
"""

from __future__ import annotations

from dataclasses import dataclass
import csv

import docs
import csvfile
import memberdata
import waiverrec
import keys


def check_waiver(membership: memberdata.Membership, 
                 groups: waiverrec.MemberWaiverGroups, 
                 waiver: docs.MemberWaiver) -> bool:
    """
    Return True if waiver is considered to be complete.
    A complete waiver is one that includes all minors of the signatory
    """
    name = waiver.signatures[0].name
    account = membership.get_account_by_fullname(name)

    if account is None:
        if not waiver.reviewed:
            print(f"Warning: no account for name in waiver'{name}'")
        return False

    family_record = groups.find_family_record(name)
    if family_record is None:
        # No minors in the family
        return True

    # TODO: check names
    return len(family_record.minors) <= len(waiver.minors)


def check_attestation(membership: memberdata.Membership, 
                      groups: waiverrec.MemberWaiverGroups, 
                      attest: docs.Attestation) -> bool:
    """
    Return True if an attestaton waiver is considered complete
    A complete waiver is one that includes all minors of the signatory
    """
    name = attest.adults[0].name
    account = membership.get_account_by_fullname(name)

    if account is None:
        if not attest.reviewed:
            print(f"Warning: no account for name in attest'{name}'")
        return False

    family_record = groups.find_family_record(name)
    if family_record is None:
        # No minors in the family
        return True

    # TODO: check names
    return len(family_record.minors) <= len(attest.minors)



def update_waivers_complete(membership: memberdata.Membership, 
                            waiver_groups: waiverrec.MemberWaiverGroups, 
                            waiver_docs: list[docs.MemberWaiver],
                            attest_docs: list[docs.Attestation]) -> None:

    # Determine if a waiver and attestation cover the minor children
    for waiver_doc in waiver_docs:
        complete = check_waiver(membership, waiver_groups, waiver_doc)
        waiver_doc.set_complete(complete)
    for attest_doc in attest_docs:
        complete = check_attestation(membership, waiver_groups, attest_doc)
        attest_doc.set_complete(complete)


def review_member_waiver_docs(membership: memberdata.Membership, waiver_docs: list[docs.MemberWaiver]) -> None:
    print("Reviewing member waiver documents")
    for waiver_doc in waiver_docs:
        account_num = ''
        for signature in waiver_doc.signatures:
            member = membership.get_one_member_by_fullname(signature.name, False)
            if member is None:
                if not waiver_doc.is_reviewed():
                    print(f"Warning: No member found for waiver signature {signature.name} in {waiver_doc.web_view_link}")
                continue
            if account_num == '':
                account_num = member.account_num 
            if account_num != member.account_num:
                print(f"Error: signatures from different accounts {signature.name}")


def review_member_attest_docs(membership: memberdata.Membership, attest_docs: list[docs.Attestation]) -> None:
    print("Reviewing member attestation documents")
    for attest_doc in attest_docs:
        if len(attest_doc.adults) < 1:
            print(f"Warning: missing a signatory in {attest_doc.web_view_link}")
        else:
            adult = attest_doc.adults[0]
            member = membership.get_one_member_by_fullname(adult.name, False)
            if member is None and not attest_doc.is_reviewed():
                print(f"Warning: No member found for attest signature {adult.name} in {attest_doc.web_view_link}")


def review_and_update_waivers(membership: memberdata.Membership,
                              waiver_groups: waiverrec.MemberWaiverGroups,
                              waiver_docs: list[docs.MemberWaiver],
                              attest_docs: list[docs.Attestation]) -> None:
    """
    Review all of the attestation and waiver documents - check for inconsistencies / errors.
    Update minor complete status reflecting if all minors are covered
    """
    review_member_waiver_docs(membership, waiver_docs)
    review_member_attest_docs(membership, attest_docs)
    update_waivers_complete(membership, waiver_groups, waiver_docs, attest_docs)


def create_waiver_doc_map(member_waivers: list[docs.MemberWaiver]) -> dict[str,docs.MemberWaiver]:
    """
    Create a dictionary of preferred waiver docs for each person.
    We find the best waiver associated with a person.
    """
    doc_map: dict[str, docs.MemberWaiver] = {}
    for waiver_doc in member_waivers:
        for signature in waiver_doc.signatures:
            # Use lower case name
            name = signature.name.lower()
            current_waiver_doc = doc_map.get(name)

            # If no waiver yet identified, take this one
            if current_waiver_doc is None:
                doc_map[name] = waiver_doc
                continue

            # Don't replace a family waiver with an individual
            if current_waiver_doc.type != docs.MemberWaiver.TYPE_FAMILY:
                doc_map[name] = waiver_doc
                continue

            # Prefer the complete waiver
            if not current_waiver_doc.is_complete():
                doc_map[name] = waiver_doc

    return doc_map

def create_attest_doc_map(attestations: list[docs.Attestation]) -> dict[str, docs.Attestation]:
    """
    Create a dictionary of preffered attest docs for each person
    """
    doc_map: dict[str, docs.Attestation] = {}
    for attestation in attestations:
        # Use lower case name
        name = attestation.adults[0].name.lower()

        # Handle mutliple docs
        current_doc = doc_map.get(name)

        if current_doc is None:
            doc_map[name] = attestation
            continue

        # Don't replace a complete attestation with an incomplete
        if not current_doc.is_complete():
            doc_map[name] = attestation

    return doc_map

def update_waiver_record_status(waiver_groups: waiverrec.memberwaivergroups,
                                member_waivers: list[docs.memberwaiver],
                                attestations: list[docs.attestation]) -> None:
    """
    Determine and update the status for each desired waiver.
    Use the member waivers and attestations to update the status of each
    desired waiver.
    """
    print("Note: updating waiver records status")

    # Preferred waivers per person (lower case names)
    waiver_doc_map = create_waiver_doc_map(member_waivers)
    # Preferred attestation per person (lower case names)
    attest_doc_map = create_attest_doc_map(attestations)

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
        all_signed: bool = True

        for index, adult in enumerate(family_record.adults):
            family_record.signatures[index] = False
            name = adult.name.fullname().lower()

            # Check attest doc 
            attest_doc = attest_doc_map.get(name)
            if attest_doc is not None:
                family_record.web_links[index] = attest_doc.web_view_link
                if attest_doc.is_complete():
                    family_record.signatures[index] = True

            # Check if signed and complete 
            waiver_doc = waiver_doc_map.get(name)
            if waiver_doc is not None:
                family_record.web_links[index] = waiver_doc.web_view_link
                if waiver_doc.is_complete():
                    family_record.signatures[index] = True

            if not family_record.signatures[index]:
                all_signed = False

        family_record.signed = all_signed

def generate_single_signer_request(adult_records: list[waiverrec.AdultRecord],
                                   member_keys: keys.MemberKeys) -> None:
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    MEMBER_ID = csvfile.MEMBER_ID
    FIELD_KEY = waiverrec.MemberRecord.FIELD_HAS_KEY
    FIELD_KEY_ENABLED = waiverrec.MemberRecord.FIELD_KEY_ENABLED
    FIELD_NAME = waiverrec.AdultRecord.FIELD_NAME
    FIELD_EMAIL = waiverrec.AdultRecord.FIELD_EMAIL

    HEADER = [ ACCOUNT_NUM, MEMBER_ID,
              FIELD_KEY,
              FIELD_KEY_ENABLED,
              FIELD_NAME, FIELD_EMAIL ]

    rows: list[dict[str,str]] = []

    for record in adult_records:
        # Check if anyone has a key
        has_key = member_keys.has_key(record.member.member_id)
        key_enabled = member_keys.has_enabled_key(record.member.member_id)
        if not record.signed:
            # Create a row
            row = { ACCOUNT_NUM: record.member.account_num,
                MEMBER_ID: record.member.member_id,
                FIELD_KEY: has_key,
                FIELD_KEY_ENABLED: key_enabled,
                FIELD_NAME: record.member.name.fullname(),
                FIELD_EMAIL: record.member.email
               }
            rows.append(row)

    csv_file = "output/single_signer_request.csv" 
    if not csvfile.backup_file(csv_file):
        return

    print(f"Note: write {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()


def generate_single_signer_family_request(family_records: list[waiverrec.FamilyRecord],
                                          member_keys: keys.MemberKeys) -> None:
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    MEMBER_ID = csvfile.MEMBER_ID
    FIELD_KEY = waiverrec.MemberRecord.FIELD_HAS_KEY
    FIELD_KEY_ENABLED = waiverrec.MemberRecord.FIELD_KEY_ENABLED
    FIELD_NAME = waiverrec.AdultRecord.FIELD_NAME
    FIELD_EMAIL = waiverrec.AdultRecord.FIELD_EMAIL
    FIELD_MINOR1 = waiverrec.FamilyRecord.FIELD_MINOR1
    FIELD_MINOR2 = waiverrec.FamilyRecord.FIELD_MINOR2
    FIELD_MINOR3 = waiverrec.FamilyRecord.FIELD_MINOR3
    FIELD_MINOR4 = waiverrec.FamilyRecord.FIELD_MINOR4
    FIELD_MINOR5 = waiverrec.FamilyRecord.FIELD_MINOR5

    HEADER = [ ACCOUNT_NUM, MEMBER_ID,
              FIELD_KEY,
              FIELD_KEY_ENABLED,
              FIELD_NAME, FIELD_EMAIL,
              FIELD_MINOR1, 
              FIELD_MINOR2, 
              FIELD_MINOR3, 
              FIELD_MINOR4, 
              FIELD_MINOR5 ]

    rows: list[dict[str,str]] = []

    for record in family_records:
        # Check if anyone has a key
        has_key = False
        key_enabled = False
        for adult in record.adults:
            has_key = has_key or member_keys.has_key(adult.member_id)
            key_enabled = key_enabled or member_keys.has_enabled_key(adult.member_id)

        for minor in record.minors:
            has_key = has_key or member_keys.has_key(minor.member_id)
            key_enabled = key_enabled or member_keys.has_enabled_key(minor.member_id)

        for index, adult in enumerate(record.adults):
            if not record.signatures[index]:
                # Create a row
                row = { ACCOUNT_NUM: adult.account_num,
                        MEMBER_ID: adult.member_id,
                        FIELD_KEY: has_key,
                        FIELD_KEY_ENABLED: key_enabled,
                        FIELD_NAME: adult.name.fullname(),
                        FIELD_EMAIL: adult.email
                       }
                for minor_index, minor in enumerate(record.minors):
                    row[HEADER[minor_index + 6]] = minor.name.fullname()
                rows.append(row)

    csv_file = "output/single_signer_family_request.csv" 
    if not csvfile.backup_file(csv_file):
        return

    print(f"Note: write {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()


def generate_member_records(waiver_groups: waiverrec.memberwaivergroups,
                            member_keys: keys.MemberKeys) -> None:
    member_records: list[waiverrec.MemberRecord] = []
    member_records = waiverrec.MemberRecord.gen_records(waiver_groups, member_keys)
    print("Note: writing member records CSV")
    waiverrec.MemberRecord.write_csv(member_records, waiverrec.MemberRecord.member_csv)

    
def report_waiver_record_stats(membership: memberdata.Membership,
                        waiver_groups: waiverrec.MemberWaiverGroups,
                        member_waivers: list[docs.MemberWaiver],
                        attestations: list[docs.Attestation],
                        member_keys: dict[str, keys.KeyEntry]) -> None:


    unwaivered_adult_with_keys_count: int = 0   # No minors
    unwaivered_adult_with_enabled_keys_count: int = 0   # No minors
    unwaivered_adult_count: int = 0             # No minors

    waivered_family_count: int = 0
    unwaivered_family_count: int = 0
    unwaivered_family_with_keys_count: int = 0
    unwaivered_family_with_enabled_keys_count: int = 0
    waivered_family_members: int = 0
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

    for family_record in waiver_groups.with_minor_children:
        has_key = False
        key_enabled = False
        for index, adult in enumerate(family_record.adults):
            if adult.member_id in member_keys:
                has_key = True
                if member_keys[adult.member_id].enabled:
                    key_enabled = True

        for minor in family_record.minors:
            if minor.member_id in member_keys:
                has_key = True
                if member_keys[minor.member_id].enabled:
                    key_enabled = True
 
        if family_record.signed:
            waivered_family_count += 1
            waivered_minors += len(family_record.minors)
            waivered_family_members += (len(family_record.adults) + len(family_record.minors))
        else:
            unwaivered_family_count += 1
            unwaivered_family_members += (len(family_record.adults) + len(family_record.minors))
            if has_key:
                unwaivered_family_with_keys_count += 1
            if key_enabled:
                unwaivered_family_with_enabled_keys_count += 1

    for waiver in waiver_groups.no_minor_children:
        if waiver.signed:
            waivered_adults += 1
        else:
            unwaivered_adult_count += 1
            if waiver.member.member_id in member_keys:
                unwaivered_adult_with_keys_count += 1
                if member_keys[waiver.member.member_id].enabled:
                    unwaivered_adult_with_enabled_keys_count += 1

    total_keys = len(member_keys)
    enabled_keys = 0
    for key_entry in member_keys.values():
        if key_entry.enabled:
            enabled_keys += 1

    print()
    print("Stats - Progress")
    print(f"Unwaivered Adults without minors: {unwaivered_adult_count}")
    print(f"Unwaivered Adults without minors with keys: {unwaivered_adult_with_keys_count}")
    print(f"Unwaivered Adults without minors with enabled keys: {unwaivered_adult_with_enabled_keys_count}")
    print()
    print(f"Waivered Families: {waivered_family_members} members in {waivered_family_count} families")
    print(f"Unwaivered Families: {unwaivered_family_members} members in {unwaivered_family_count} families, {unwaivered_family_with_keys_count} with keys")
    print(f"Unwaivered Families with enabled keys: {unwaivered_family_with_enabled_keys_count}")
    print()
    print("Totals:")
    print(f"Adults:  {waivered_adults} waivered / {total_adults} total")
    print(f"Minors: {waivered_minors} waivered / {total_minors} total")
    print(f"Members: {total_members} total")
    print(f"Members allocated keys: {enabled_keys} enabled / {total_keys} total")
    print()
    print()

def main() -> None:
    print("Usage: {sys.argv[0]} [ update ]")

    membership = memberdata.Membership()
    membership.read_csv_files()
    waiver_groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)
    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()
    member_keys = keys.MemberKeys()
    member_keys.load_keys(membership)

    review_and_update_waivers(membership, waiver_groups, member_waivers, attestations)
    update_waiver_record_status(waiver_groups, member_waivers, attestations)
    report_waiver_record_stats(membership, waiver_groups, member_waivers, attestations, member_keys)

    generate_member_records(waiver_groups, member_keys)

    waiverrec.MemberWaiverGroups.write_csv_files(waiver_groups)
    docs.MemberWaiver.write_csv(member_waivers)
    docs.Attestation.write_csv(attestations)


if __name__ == "__main__":
    main()
