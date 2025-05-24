"""
Determine sets of members for bulk requests of waiver signatures.

This automates trying to determine which people are parents that need to sign
family waivers, and which minors are include on the waiver.

3 types of results
- families with minor children  - request family waiver
- adults with no minor children - request signature of single person on a waiver
- unclear on parents - figure out who are parents, update parents.csv until empty

Outputs:
- parent_list_to_sign.csv
- adult_list_to_sign.csv
- unknown_list_to_sign.csv
"""

from __future__ import annotations

import csv
import os

import csvfile
import memberdata
from memberdata import MemberEntry
import keys

class AdultRecord:
    """
    Represents a single signer for a waiver
    """
    def __init__(self, member: MemberEntry):
        self.member = member
        self.key_address = ""
        self.signed = False
        self.web_link: str = ""

    FIELD_NAME = "name"
    FIELD_EMAIL = "email_address"
    FIELD_KEY_EMAIL = "key_email"
    FIELD_WEB_LINK = "web_link"

    @staticmethod
    def get_header() -> list[str]:
        return [ csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, csvfile.SIGNED,
                AdultRecord.FIELD_NAME, AdultRecord.FIELD_EMAIL, AdultRecord.FIELD_KEY_EMAIL, AdultRecord.FIELD_WEB_LINK]

    def get_row(self):
        row = {}
        row[csvfile.ACCOUNT_NUM] = self.member.account_num
        row[csvfile.MEMBER_ID] = self.member.member_id
        row[csvfile.SIGNED] = csvfile.signed_str(self.signed)
        row[AdultRecord.FIELD_NAME] = self.member.name.fullname()
        row[AdultRecord.FIELD_EMAIL] = self.member.email
        row[AdultRecord.FIELD_KEY_EMAIL] = self.key_address
        row[AdultRecord.FIELD_WEB_LINK] = self.web_link
        return row

    @staticmethod
    def read_row(membership: memberdata.Membership, row: dict[str,str]) -> AdultRecord|None:
        member_id = row[csvfile.MEMBER_ID]
        name = row[AdultRecord.FIELD_NAME]
        member_entry = membership.get_member_by_id(member_id)
        if member_entry is None:
            print(f"Warning: no member id: {member_id} name: '{name}' found.")
            return None
        record = AdultRecord(member_entry)
        record.signed = csvfile.is_signed(row[csvfile.SIGNED])
        record.key_address = row[AdultRecord.FIELD_KEY_EMAIL]
        record.web_link = row[AdultRecord.FIELD_WEB_LINK]
        return record

    @staticmethod 
    def read_csv(membership: memberdata.Membership, csv_file: str) -> list[AdultRecord]:
        """
        Read AdultWaiver records from CSV file
        """
        result: list[AdultRecord] = []

        if not os.path.exists(csv_file):
            return result
        
        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = AdultRecord.read_row(membership, row)
                if record is not None:
                    result.append(record)
        return result


    @staticmethod
    def write_csv(records: list[AdultRecord], csv_file: str) -> None:
        """
        Write AdultWaiver records to a CSV file
        """
        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: Write {csv_file}")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=AdultRecord.get_header())
            writer.writeheader()
            for record in records:
                writer.writerow(record.get_row())
            f.close()

class FamilyRecord:
    """
    Represents a family or potential family for which we need more information
    """

    def __init__(self) -> None: 
        self.adults: list[MemberEntry] = []
        self.minors: list[MemberEntry] = []
        self.signed: bool = False
        self.web_link: str = ""

    FIELD_NAME ="name"
    FIELD_EMAIL = "email_address"
    FIELD_NAME2 ="name2"
    FIELD_EMAIL2 = "email_address2"
    FIELD_NAME3 ="name3"
    FIELD_EMAIL3 = "email_address3"
    FIELD_NAME4 ="name4"
    FIELD_EMAIL4 = "email_address4"

    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_MINOR5 = "minor5"

    FIELD_WEB_LINK = "web_link"

    HEADER = [ csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, csvfile.SIGNED,
              FIELD_NAME, FIELD_EMAIL,
              FIELD_NAME2, FIELD_EMAIL2,
              FIELD_NAME3, FIELD_EMAIL3,
              FIELD_NAME4, FIELD_EMAIL4,
              FIELD_MINOR1 ,FIELD_MINOR2,
              FIELD_MINOR3, FIELD_MINOR4, FIELD_MINOR5, FIELD_WEB_LINK ]

    @staticmethod
    def get_header() -> list[str]:
        return FamilyRecord.HEADER
   
    def get_row(self):
        row = {}
        if len(self.adults) == 0:
            return row

        row[csvfile.ACCOUNT_NUM] = self.adults[0].account_num
        row[csvfile.MEMBER_ID] = self.adults[0].member_id
        row[csvfile.SIGNED] = csvfile.signed_str(self.signed)
        row[FamilyRecord.FIELD_WEB_LINK] = self.web_link
        for i, member in enumerate(self.adults):
            row[FamilyRecord.HEADER[i * 2 + 3]] = member.name.fullname()
            row[FamilyRecord.HEADER[i * 2 + 4]] = member.email
        for i, minor in enumerate(self.minors):
            row[FamilyRecord.HEADER[i + 11]] = minor.name.fullname()
        return row

    @staticmethod
    def read_row(membership: memberdata.Membership, row: dict[str, str]) -> FamilyRecord|None:
        member_id = row[csvfile.MEMBER_ID]
        name = row[FamilyRecord.FIELD_NAME]
        member_entry = membership.get_member_by_id(member_id)
        if member_entry is None:
            print(f"Warning: no member id: {member_id} name: '{name}' found.")
            return None

        record = FamilyRecord()
        record.signed = csvfile.is_signed(row[csvfile.SIGNED])
        record.web_link = row[FamilyRecord.FIELD_WEB_LINK]
        record.adults.append(member_entry)

        for index in range(5, 10, 2):
            name = row[FamilyRecord.HEADER[index]]
            if len(name.strip()) > 0:
                member_entry = membership.get_one_member_by_fullname(name, False)
                if member_entry is not None:
                    record.adults.append(member_entry)

       
        for index in range(11, 16):
            name = row[FamilyRecord.HEADER[index]]
            if len(name.strip()) > 0:
                member_entry = membership.get_one_member_by_fullname(name, True)
                if member_entry is not None:
                    record.minors.append(member_entry)

        return record
    
    @staticmethod 
    def read_csv(membership: memberdata.Membership, csv_file: str) -> list[FamilyRecord]:
        """
        Read CSV file of family waiver records
        """
        result: list[FamilyRecord] = []

        if not os.path.exists(csv_file):
            return result
        
        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = FamilyRecord.read_row(membership, row)
                if record is not None:
                    result.append(record)
        return result

    @staticmethod
    def write_csv(records: list[FamilyRecord], csv_file: str) -> None:
        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: Write {csv_file}")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FamilyRecord.get_header())
            writer.writeheader()
            for record in records:
                writer.writerow(record.get_row())
            f.close()
        

class MemberWaiverGroups:
    """
    Results of generating groupings for member waiver requests
    """

    def __init__(self) -> None:
        # Adult members with no minor children as members
        self.no_minor_children: list[AdultRecord] = []

        # Parents and minor children
        self.with_minor_children: list[FamilyRecord] = []

        # Adults potentially with minor children and minor children
        self.unknown_status: list[FamilyRecord] = []

        # Statistics for membership
        self.no_minors_count = 0
        self.unknown_parents_count = 0
        self.known_parents_count = 0

    def find_adult_record(self, name: str) -> AdultRecord|None:
        for record in self.no_minor_children:
            if record.member.name.fullname() == name:
                return record
        return None
    
    def find_family_record(self, name: str) -> FamilyRecord|None:
        for record in self.with_minor_children:
            for adult in record.adults:
                if adult.name.fullname() == name:
                    return record
        return None

    adult_waiver_filename = "output/adult_records.csv"
    familey_waiver_filename = "output/family_records.csv"
    unknown_waiver_filename = "output/unknown_families.csv"

    @staticmethod
    def read_csv_files(membership: memberdata.Membership) -> MemberWaiverGroups:
        groupings = MemberWaiverGroups()
        groupings.no_minor_children = AdultRecord.read_csv(membership, MemberWaiverGroups.adult_waiver_filename)
        groupings.with_minor_children = FamilyRecord.read_csv(membership, MemberWaiverGroups.familey_waiver_filename)
        groupings.unknown_status = FamilyRecord.read_csv(membership, MemberWaiverGroups.unknown_waiver_filename)
        return groupings

    def write_csv_files(self) -> None:
        AdultRecord.write_csv(self.no_minor_children, MemberWaiverGroups.adult_waiver_filename)
        FamilyRecord.write_csv(self.with_minor_children, MemberWaiverGroups.familey_waiver_filename)
        FamilyRecord.write_csv(self.unknown_status, MemberWaiverGroups.unknown_waiver_filename)
 

def simple_test() -> None:
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.gen_member_key_map(membership)

    adult_records: list[AdultRecord] = []
    family_records: list[FamilyRecord] = []

    for account in membership.active_member_accounts():
        members = membership.get_members_for_account_num(account.account_num)
        if membership.has_minor_children(account.account_num):
            family_record = FamilyRecord()
            for member in members:
                if not member.is_minor():
                    family_record.adults.append(member)
                else:
                    family_record.minors.append(member)
            family_records.append(family_record)
        else:
            for member in members:
                adult_record = AdultRecord(member)
                if member.member_id in member_keys:
                    adult_record.key_address = member_keys[member.member_id].member_email
                adult_records.append(adult_record)

    family_csv = "test/family_records.csv"
    adult_csv = "test/adult_records.csv"

    FamilyRecord.write_csv(family_records, family_csv)
    AdultRecord.write_csv(adult_records, adult_csv)

    families = FamilyRecord.read_csv(membership, family_csv)
    adults = AdultRecord.read_csv(membership, adult_csv)

    assert len(families) == len(family_records)
    assert len(adults) == len(adult_records)

    FamilyRecord.write_csv(families, family_csv)
    AdultRecord.write_csv(adults, adult_csv)

    families = FamilyRecord.read_csv(membership, family_csv)
    adults = AdultRecord.read_csv(membership, adult_csv)

    assert len(families) == len(family_records)
    assert len(adults) == len(adult_records)




if __name__ == "__main__":
    simple_test()
    

