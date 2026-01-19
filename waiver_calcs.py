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
import attest_calcs


def check_waiver(membership: memberdata.Membership, 
                 groups: waiverrec.RequiredWaivers, 
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
                      groups: waiverrec.RequiredWaivers, 
                      attest: docs.Attestation) -> bool:
    """
    Return True if an attestaton waiver is considered complete
    A complete waiver is one that includes all minors of the signatory
    """
    name = attest.adult().name
    account = membership.get_account_by_fullname(name)

    if account is None:
        if not attest.reviewed:
            print(f"Warning: no account for name in attest'{name}'")
        return attest.is_complete()

    family_record = groups.find_family_record(name)
    if family_record is None:
        # No minors in the family
        return True

    # TODO: check names
    return len(family_record.minors) <= len(attest.minors)



def update_waivers_complete(membership: memberdata.Membership, 
                            waiver_groups: waiverrec.RequiredWaivers, 
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
            adult = attest_doc.adult()
            member = membership.get_one_member_by_fullname(adult.name, False)
            if member is None and not attest_doc.is_reviewed():
                print(f"Warning: No member found for attest signature {adult.name} in {attest_doc.web_view_link}")


def review_and_update_waivers(membership: memberdata.Membership,
                              waiver_groups: waiverrec.RequiredWaivers,
                              waiver_docs: list[docs.MemberWaiver],
                              attest_docs: list[docs.Attestation]) -> None:
    """
    Review all of the attestation and waiver documents - check for inconsistencies / errors.
    Update minor complete status reflecting if all minors are covered
    """
    review_member_waiver_docs(membership, waiver_docs)
    review_member_attest_docs(membership, attest_docs)
    update_waivers_complete(membership, waiver_groups, waiver_docs, attest_docs)


def create_waiver_doc_map(membership: memberdata.Membership, member_waivers: list[docs.MemberWaiver]) -> dict[str,docs.MemberWaiver]:
    """
    Create a dictionary of preferred waiver docs for each person mapped by ID.
    We find the best waiver associated with a person.
    """
    doc_map: dict[str, docs.MemberWaiver] = {}
    for waiver_doc in member_waivers:
        for signature in waiver_doc.signatures:
            member_name = memberdata.MemberName.CreateMemberName(signature.name)
            if member_name is None:
                if not waiver_doc.reviewed:
                    print(f"Warning: unable to parse waiver signature {signature.name} in {waiver_doc.web_view_link}")
                continue
            member = membership.find_one_member_by_name(member_name)
            if member is None:
                if not waiver_doc.reviewed:
                    print(f"Warning: unable to find member for waiver signature {signature.name} in {waiver_doc.web_view_link}")
                continue
            current_waiver_doc = doc_map.get(member.member_id)

            # If no waiver yet identified, take this one
            if current_waiver_doc is None:
                doc_map[member.member_id] = waiver_doc
                continue

            # Don't replace a family waiver with an individual
            if current_waiver_doc.type != docs.MemberWaiver.TYPE_FAMILY:
                doc_map[member.member_id] = waiver_doc
                continue

            # Prefer the complete waiver
            if not current_waiver_doc.is_complete():
                doc_map[member.member_id] = waiver_doc

    return doc_map

def create_attest_doc_map(membership: memberdata.Membership, attestations: list[docs.Attestation]) -> dict[str, docs.Attestation]:
    """
    Create a dictionary of preffered attest docs for each person by member_id
    """
    doc_map: dict[str, docs.Attestation] = {}
    for attestation in attestations:
        # Use lower case name
        name = attestation.adult().name

        member_name = memberdata.MemberName.CreateMemberName(name)
        if member_name is None:
            if not attestation.reviewed:
                print(f"Warning: unable to parse attest signature {name} in {attestation.web_view_link}")
            continue
        member = membership.find_one_member_by_name(member_name)
        if member is None:
            if not attestation.reviewed:
                print(f"Warning: unable to find member for attest signature {name} in {attestation.web_view_link}")
            continue
 
        # Handle mutliple docs
        current_doc = doc_map.get(member.member_id)

        if current_doc is None:
            doc_map[member.member_id] = attestation
            continue

        # Don't replace a complete attestation with an incomplete
        if not current_doc.is_complete():
            doc_map[member.member_id] = attestation

    return doc_map

def update_waiver_record_status(membership: memberdata.Membership,
                                waiver_groups: waiverrec.RequiredWaivers,
                                member_waivers: list[docs.MemberWaiver],
                                attestations: list[docs.Attestation]) -> None:
    """
    Determine and update the status for each desired waiver.
    Use the member waivers and attestations to update the status of each
    desired waiver.
    """
    print("Note: updating waiver records status")

    # Preferred waivers per person (lower case names)
    waiver_doc_map = create_waiver_doc_map(membership, member_waivers)
    # Preferred attestation per person (lower case names)
    attest_doc_map = create_attest_doc_map(membership, attestations)

    # Update the signed state of waviers 
    for adult_record in waiver_groups.no_minor_children:
        adult_record.signed = False

        waiver_doc = waiver_doc_map.get(adult_record.adult().member_id)
        if waiver_doc is not None:
            adult_record.web_links[0] = waiver_doc.web_view_link
            adult_record.signatures[0] = waiver_doc.is_complete() 
            adult_record.signed = waiver_doc.is_complete()
            continue

        attest_doc = attest_doc_map.get(adult_record.adult().member_id)
        if attest_doc is not None:
            adult_record.web_links[0] = attest_doc.web_view_link
            adult_record.signatures[0] = attest_doc.is_complete() 
            adult_record.signed = True

    # Update signed state of family waivers
    for family_record in waiver_groups.with_minor_children:
        all_signed: bool = True

        for index, adult in enumerate(family_record.adults):
            family_record.signatures[index] = False

            # Check attest doc 
            attest_doc = attest_doc_map.get(adult.member_id)
            if attest_doc is not None:
                family_record.web_links[index] = attest_doc.web_view_link
                if attest_doc.is_complete():
                    family_record.signatures[index] = True

            # Check if signed and complete 
            waiver_doc = waiver_doc_map.get(adult.member_id)
            if waiver_doc is not None:
                family_record.web_links[index] = waiver_doc.web_view_link
                if waiver_doc.is_complete():
                    family_record.signatures[index] = True

            if not family_record.signatures[index]:
                all_signed = False

        family_record.signed = all_signed

def generate_single_signer_request(membership: memberdata.Membership, adult_records: list[waiverrec.RequiredWaiver]) -> None:
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    MEMBER_ID = csvfile.MEMBER_ID
    FIELD_KEY = waiverrec.RequiredWaiver.FIELD_HAS_KEY
    FIELD_KEY_ENABLED = waiverrec.RequiredWaiver.FIELD_KEY_ENABLED
    FIELD_ATTEST = "attest_req"
    FIELD_NAME = "name"
    FIELD_EMAIL = "email"

    HEADER = [ ACCOUNT_NUM, MEMBER_ID,
              FIELD_KEY,
              FIELD_KEY_ENABLED,
              FIELD_ATTEST,
              FIELD_NAME, FIELD_EMAIL ]

    rows: list[dict[str,str]] = []

    for record in adult_records:
        # Check if anyone has a key
        if not record.signed:
            # Create a row

            # Note if this member is already been requested to sign an attestation
            attest_requested = False
            primary_member = membership.get_primary_account_member(record.adult().account_num)
            if primary_member is not None and primary_member.member_id == record.adult().member_id:
                attest_requested = True
           
            row = { ACCOUNT_NUM: record.adult().account_num,
                MEMBER_ID: record.adult().member_id,
                FIELD_KEY: record.has_key,
                FIELD_KEY_ENABLED: record.key_enabled,
                FIELD_ATTEST: attest_requested,
                FIELD_NAME: record.adult().name.fullname(),
                FIELD_EMAIL: record.adult().email
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


def generate_single_signer_family_request(membership: memberdata.Membership, family_records: list[waiverrec.RequiredWaiver]) -> None:
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    MEMBER_ID = csvfile.MEMBER_ID
    FIELD_KEY = waiverrec.MemberRecord.FIELD_HAS_KEY
    FIELD_KEY_ENABLED = waiverrec.MemberRecord.FIELD_KEY_ENABLED
    FIELD_ATTEST = "attest_req"
    FIELD_NAME = "name"
    FIELD_EMAIL = "email"
    FIELD_MINOR1 = waiverrec.RequiredWaiver.FIELD_MINOR1
    FIELD_MINOR2 = waiverrec.RequiredWaiver.FIELD_MINOR2
    FIELD_MINOR3 = waiverrec.RequiredWaiver.FIELD_MINOR3
    FIELD_MINOR4 = waiverrec.RequiredWaiver.FIELD_MINOR4
    FIELD_MINOR5 = waiverrec.RequiredWaiver.FIELD_MINOR5

    HEADER = [ ACCOUNT_NUM, MEMBER_ID,
              FIELD_KEY,
              FIELD_KEY_ENABLED,
              FIELD_ATTEST,
              FIELD_NAME, FIELD_EMAIL,
              FIELD_MINOR1, 
              FIELD_MINOR2, 
              FIELD_MINOR3, 
              FIELD_MINOR4, 
              FIELD_MINOR5 ]

    rows: list[dict[str,str]] = []

    for record in family_records:
        # Check if anyone has a key
        has_key = record.has_key
        key_enabled = record.key_enabled

        for index, adult in enumerate(record.adults):
            if not record.signatures[index]:
                # Create a row

                # Note if this member is already been requested to sign an attestation
                attest_requested = False
                primary_member = membership.get_primary_account_member(adult.account_num)
                if primary_member is not None and primary_member.member_id == adult.member_id:
                    attest_requested = True
 
                row = { ACCOUNT_NUM: adult.account_num,
                        MEMBER_ID: adult.member_id,
                        FIELD_KEY: has_key,
                        FIELD_KEY_ENABLED: key_enabled,
                        FIELD_ATTEST: attest_requested,
                        FIELD_NAME: adult.name.fullname(),
                        FIELD_EMAIL: adult.email
                       }
                for minor_index, minor in enumerate(record.minors):
                    row[HEADER[minor_index + 7]] = minor.name.fullname()
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

def generate_attest_request(membership: memberdata.Membership, attest_docs: list[docs.Attestation], family_records: list[waiverrec.RequiredWaiver]) -> None:
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    MEMBER_ID = csvfile.MEMBER_ID
    FIELD_NAME = "name"
    FIELD_EMAIL = "email"
    FIELD_MINOR1 = waiverrec.RequiredWaiver.FIELD_MINOR1
    FIELD_MINOR2 = waiverrec.RequiredWaiver.FIELD_MINOR2
    FIELD_MINOR3 = waiverrec.RequiredWaiver.FIELD_MINOR3
    FIELD_MINOR4 = waiverrec.RequiredWaiver.FIELD_MINOR4
    FIELD_MINOR5 = waiverrec.RequiredWaiver.FIELD_MINOR5

    HEADER = [ ACCOUNT_NUM, MEMBER_ID,
              FIELD_NAME, FIELD_EMAIL,
              FIELD_MINOR1, 
              FIELD_MINOR2, 
              FIELD_MINOR3, 
              FIELD_MINOR4, 
              FIELD_MINOR5 ]

    rows: list[dict[str,str]] = []

    attest_doc_map = create_attest_doc_map(membership, attest_docs)

    for account in membership.active_member_accounts():
        primary_member = membership.get_primary_account_member(account.account_num)
        if primary_member is None:
            print(f"Warning: skipping attest req for account {account.account_num}")
            continue

        attest_signed = False
        for member in membership.get_members_for_account_num(account.account_num):
            attest_doc = attest_doc_map.get(member.member_id)
            if attest_doc is not None and attest_doc.is_complete():
                attest_signed = True

        if attest_signed:
            continue

        row = { ACCOUNT_NUM: primary_member.account_num,
                MEMBER_ID: primary_member.member_id,
                FIELD_NAME: primary_member.name.fullname(),
                FIELD_EMAIL: primary_member.email
               }

        # Search for minor children
        family_record = None
        for record in family_records:
            for adult in record.adults:
                if adult.member_id == primary_member.member_id:
                    family_record = record
                    break

        if family_record is not None:
            for minor_index, minor in enumerate(family_record.minors):
                row[HEADER[minor_index + 4]] = minor.name.fullname()
        rows.append(row)

    csv_file = "output/attestation_request.csv" 
    if not csvfile.backup_file(csv_file):
        return

    print(f"Note: write {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()


# TODO: Add support for signature requested tracking
# Read name and email from a CSV file - save in data/sigs_requested - include date
#   - new module: update_requested <csv file>
# Read data/sigs_requested and include a field in the signature_request files

def generate_account_status(membership: memberdata.Membership,
                            attestations: list[docs.Attestation],
                            waiver_groups: waiverrec.RequiredWaivers,
                            member_keys: keys.MemberKeys):
    # Output:
    # Account#, Primary Last Name, #keys, #keys enabled, attest status, minors waivered status, unwaivered keys, all waivered
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    NAME = "Name"
    ATTEST = "Attestation Status"
    NUM_KEYS = "Number of Keys"
    KEYS_ENABLED = "Keys Enabled"
    MINORS_WAIVERED = "Minors Waivered"
    UNWAIVERED_KEYS = "Keys w/o Waivers"
    ALL_WAIVERED = "All Waivered"


    attest_calcs.record_attestations(membership, attestations)
    waiver_map = {}
    for waiver in waiver_groups.no_minor_children:
        if waiver.account_num() not in waiver_map:
            waiver_map[waiver.account_num()] = []
        waiver_map[waiver.account_num()].append(waiver)

    for waiver in waiver_groups.with_minor_children:
        if waiver.account_num() not in waiver_map:
            waiver_map[waiver.account_num()] = []
        waiver_map[waiver.account_num()].append(waiver)

    # CSV Rows to write
    rows = []

    # Iterate through active accounts
    for account in membership.active_member_accounts():
        # check status of attestation
        attest_status = "None"
        attest = attest_calcs.get_account_attest(account.account_num)
        if attest is not None:
            if attest_calcs.get_attest_status(membership, attest):
                attest_status = "Good"
            else:
                attest_status = "Present"
    
        # review waivers
        waivers = waiver_map.get(account.account_num, [])
        num_minors = 0
        minors_waivered = True
        unwaivered_keys = False
        all_waivered = True

        for waiver in waivers:
            # check minors waivered - family waiver
            if waiver.has_minors():
                num_minors = len(waiver.minors)
                minors_waivered = waiver.signed

            # check adult waivers - all members
            if not waiver.signed:
                all_waivered = False
                if waiver.key_enabled:
                    unwaivered_keys = True

        # gather key data - all members
        num_keys = 0
        num_enabled_keys = 0

        for member in membership.get_members_for_account_num(account.account_num):
            if member_keys.has_key(member.member_id):
                num_keys += 1
            if member_keys.has_enabled_key(member.member_id):
                num_enabled_keys += 1

        row = { ACCOUNT_NUM : account.account_num,
                NAME : account.billing_name.last_name,
                ATTEST : attest_status,
                MINORS_WAIVERED  : minors_waivered,
                UNWAIVERED_KEYS : unwaivered_keys,
                NUM_KEYS : num_keys,
                KEYS_ENABLED : num_enabled_keys,
               ALL_WAIVERED : all_waivered }
        rows.append(row)

    # Report
    csv_file = "output/account_status.csv" 
    if not csvfile.backup_file(csv_file):
        return

    HEADER = [ ACCOUNT_NUM,
               NAME,
               ATTEST,
               NUM_KEYS,
               KEYS_ENABLED,
               MINORS_WAIVERED,
               UNWAIVERED_KEYS,
               ALL_WAIVERED ]

    print(f"Note: write {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()



def generate_member_records(waiver_groups: waiverrec.RequiredWaivers, member_keys: keys.MemberKeys) -> None:
    member_records: list[waiverrec.MemberRecord] = []
    member_records = waiverrec.MemberRecord.gen_records(waiver_groups, member_keys)
    print("Note: writing member records CSV")
    waiverrec.MemberRecord.write_csv(member_records, waiverrec.MemberRecord.member_csv)

#TODO: should no longer need member_keys here    
def report_waiver_record_stats(membership: memberdata.Membership,
                        waiver_groups: waiverrec.RequiredWaivers,
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
        has_key = family_record.has_key
        key_enabled = family_record.key_enabled

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
            if waiver.adult().member_id in member_keys:
                unwaivered_adult_with_keys_count += 1
                if member_keys[waiver.adult().member_id].enabled:
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

