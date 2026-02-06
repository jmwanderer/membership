"""
Functions to generate output reports
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
import waiver_calcs



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
    """
    Generate a CSV to use to make signature requests for attestations.
    Uses the primary member name and email and includes minors on the
    acount if we want to pre-populate the waiver.
    """
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

    attest_doc_map = waiver_calcs.create_attest_doc_map(membership, attest_docs)

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


def generate_key_status(membership: memberdata.Membership,
                        member_keys: keys.MemberKeys) -> None:
    # Output: MemberID, AccountNum, Name, Email, Issue, KeyExternID
    MEMBER_ID = csvfile.MEMBER_ID
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    NAME = "Name"
    EMAIL = "Email"
    ENABLED = "Enabled"
    ISSUE = "Issue"
    KEYID = "ExternKeyID"

    def create_row(key_entry: keys.KeyEntry) -> dict[str, str]:
        return { MEMBER_ID: key_entry.member_id,
                 ACCOUNT_NUM: key_entry.account_num,
                 NAME: key_entry.member_name.fullname(),
                 EMAIL: key_entry.member_email,
                 ENABLED: csvfile.bool_str(key_entry.enabled),
                 KEYID: key_entry.key_id }

    rows = []
    for key_entry in member_keys.key_entries():
        if key_entry.is_staff():
            continue

        if key_entry.account_num not in membership.account_nums():
            row = create_row(key_entry)
            row[ISSUE] = "Invalid account number"
            rows.append(row)
            continue

        account = membership.get_account(key_entry.account_num)
        if not account.is_active_member() and not account.is_staff():
            row = create_row(key_entry)
            row[ISSUE] = "Key held by non-active account"
            rows.append(row)
            continue

        member_entries = membership.find_members_by_name(key_entry.member_name)
        if len(member_entries) < 1:
            row = create_row(key_entry)
            row[ISSUE] = "Invalid member name"
            rows.append(row)
            continue

        account_num = member_entries[0].account_num 
        if account_num != key_entry.account_num:
            row = create_row(key_entry)
            row[ISSUE] = f"Key account number does not match user account number {account_num}"
            rows.append(row)
            continue
    
    # Write the report
    csv_file = "output/key_status.csv" 

    HEADER = [ MEMBER_ID,
               ACCOUNT_NUM,
               NAME,
               EMAIL,
               ENABLED,
               ISSUE,
               KEYID ]

    print(f"Note: write {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()


def generate_account_status(membership: memberdata.Membership,
                            attestations: list[docs.Attestation],
                            waiver_groups: waiverrec.RequiredWaivers,
                            member_keys: keys.MemberKeys):
    # Output:
    # Account#, Primary Last Name, #keys, #keys enabled, attest status, minors waivered status, unwaivered keys, all waivered
    ACCOUNT_NUM = csvfile.ACCOUNT_NUM
    NAME = "Name"
    EMAIL = "Email"
    ATTEST = "Attestation Status"
    NUM_KEYS = "Number of Keys"
    KEYS_ENABLED = "Keys Enabled"
    MINORS_WAIVERED = "Minors Waivered"
    UNWAIVERED_KEYS = "Keys w/o Waivers"
    ALL_WAIVERED = "All Waivered"


    # Save attest date for later use
    attest_calcs.record_attestations(membership, attestations)

    # Build map of account numbers to waivers
    waiver_map: dict[str,list[waiverrec.RequiredWaiver]] = {}
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
                attest_status = "Inconsistent"
    
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
                EMAIL : account.email,
                ATTEST : attest_status,
                MINORS_WAIVERED  : minors_waivered,
                UNWAIVERED_KEYS : unwaivered_keys,
                NUM_KEYS : num_keys,
                KEYS_ENABLED : num_enabled_keys,
               ALL_WAIVERED : all_waivered }
        rows.append(row)

    # Write the report
    csv_file = "output/account_status.csv" 
    if not csvfile.backup_file(csv_file):
        return

    HEADER = [ ACCOUNT_NUM,
               NAME,
               EMAIL,
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

def generate_credential_update(membership: memberdata.Membership):

    rows = keys.read_key_file()
    for entry in rows:
        # Skip staff entries
        if entry[keys.USER_NAME].lower().startswith("staff"):
            continue

        # Check if user exists
        first_name = entry[keys.FIRST_NAME].strip()
        last_name = entry[keys.LAST_NAME].strip()
        member_name = memberdata.MemberName(first_name=first_name, last_name=last_name)
        members = membership.find_members_by_name(member_name)
        if len(members) == 0:
            print(f"Removing key for {member_name.fullname()}")
            entry[keys.REMOVE_USER] = "True"
            entry[keys.FORCE_UPDATE] = "True"
            continue

        account = membership.get_account(members[0].account_num)
        if not account.is_active_member() and entry[keys.CREDENTIAL_STATUS] == keys.ACTIVE:
            print(f"Disabling key for non-active member {member_name.fullname()}")
            entry[keys.CREDENTIAL_STATUS] = keys.INACTIVE
            entry[keys.FORCE_UPDATE] = "True"
            continue

        if not account.paid and entry[keys.CREDENTIAL_STATUS] == keys.ACTIVE:
            print(f"Disabling key for non-paid member {member_name.fullname()}")
            entry[keys.CREDENTIAL_STATUS] = keys.INACTIVE
            entry[keys.FORCE_UPDATE] = "True"
            continue

        if account.is_active_member() and account.paid and entry[keys.CREDENTIAL_STATUS] != keys.ACTIVE:
            print(f"Enabling key for member {member_name.fullname()}")
            entry[keys.CREDENTIAL_STATUS] = keys.ACTIVE
            entry[keys.FORCE_UPDATE] = "True"



    keys.write_key_file(keys.updated_keys_filename, rows)
 