"""
Model member waiver records
- requests that may be completed by a waiver doc
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
        self.has_key = False
        self.key_enabled = False
        self.signed = False
        self.web_link: str = ""

    FIELD_NAME = "name"
    FIELD_EMAIL = "email_address"
    FIELD_KEY_EMAIL = "key_email"
    FIELD_HAS_KEY = "has_key"
    FIELD_KEY_ENABLED = "key_enabled"
    FIELD_WEB_LINK = "web_link"

    @staticmethod
    def get_header() -> list[str]:
        return [ csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, csvfile.SIGNED, AdultRecord.FIELD_HAS_KEY, AdultRecord.FIELD_KEY_ENABLED,
                AdultRecord.FIELD_NAME, AdultRecord.FIELD_EMAIL, AdultRecord.FIELD_KEY_EMAIL, AdultRecord.FIELD_WEB_LINK]

    def get_row(self):
        row = {}
        row[csvfile.ACCOUNT_NUM] = self.member.account_num
        row[csvfile.MEMBER_ID] = self.member.member_id
        row[csvfile.SIGNED] = csvfile.signed_str(self.signed)
        row[AdultRecord.FIELD_HAS_KEY] = csvfile.bool_str(self.has_key)
        row[AdultRecord.FIELD_KEY_ENABLED] = csvfile.bool_str(self.key_enabled)
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
        record.has_key = csvfile.is_true_value(row[AdultRecord.FIELD_HAS_KEY])
        record.key_enabled = csvfile.is_true_value(row[AdultRecord.FIELD_KEY_ENABLED])
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
        self.signatures: list[bool] = [False, False].copy()
        self.web_links: list[str] = ["", ""].copy()
        self.minors: list[MemberEntry] = []
        self.signed: bool = False

    FIELD_NAME1 ="name1"
    FIELD_EMAIL1 = "email_address1"
    FIELD_SIGNATURE1 = "name1_signed"
    FIELD_WEB_LINK1 = "web_link1"

    FIELD_NAME2 ="name2"
    FIELD_EMAIL2 = "email_address2"
    FIELD_SIGNATURE2 = "name2_signed"
    FIELD_WEB_LINK2 = "web_link2"

    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_MINOR5 = "minor5"


    HEADER = [ csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, csvfile.SIGNED,
              FIELD_NAME1, FIELD_EMAIL1, FIELD_SIGNATURE1,
              FIELD_NAME2, FIELD_EMAIL2, FIELD_SIGNATURE2,
              FIELD_MINOR1 ,FIELD_MINOR2,
              FIELD_MINOR3, FIELD_MINOR4, FIELD_MINOR5, 
              FIELD_WEB_LINK1, FIELD_WEB_LINK2 ]

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

        member = self.adults[0]
        row[FamilyRecord.HEADER[3]] = member.name.fullname()
        row[FamilyRecord.HEADER[4]] = member.email
        row[FamilyRecord.HEADER[5]] = csvfile.signed_str(self.signatures[0])
        row[FamilyRecord.HEADER[14]] = self.web_links[0]

        if len(self.adults) > 1:
            member = self.adults[1]
            row[FamilyRecord.HEADER[6]] = member.name.fullname()
            row[FamilyRecord.HEADER[7]] = member.email
        row[FamilyRecord.HEADER[8]] = csvfile.signed_str(self.signatures[1])
        row[FamilyRecord.HEADER[15]] = self.web_links[1]

        for i, minor in enumerate(self.minors):
            row[FamilyRecord.HEADER[i + 9]] = minor.name.fullname()
        return row

    @staticmethod
    def read_row(membership: memberdata.Membership, row: dict[str, str]) -> FamilyRecord|None:
        member_id = row[csvfile.MEMBER_ID]
        name = row[FamilyRecord.FIELD_NAME1]
        member_entry = membership.get_member_by_id(member_id)
        if member_entry is None:
            print(f"Warning: no member id: {member_id} name: '{name}' found.")
            return None


        record = FamilyRecord()
        record.signed = csvfile.is_signed(row[csvfile.SIGNED])
 
        # Populate adult 1 plus signature status and web link
        record.adults.append(member_entry)
        record.signatures[0] = csvfile.is_signed(row[FamilyRecord.FIELD_SIGNATURE1])
        record.web_links[0] = row[FamilyRecord.FIELD_WEB_LINK1]

        # Populate adult 2 plus signature status and web link
        name = row[FamilyRecord.FIELD_NAME2]
        if len(name.strip()) > 0:
            member_entry = membership.get_one_member_by_fullname(name, False)
            if member_entry is not None:
                record.adults.append(member_entry)
            else:
                print(f"Warning: member in family record not found {name}")
        record.signatures[1] = csvfile.is_signed(row[FamilyRecord.FIELD_SIGNATURE2])
        record.web_links[1] = row[FamilyRecord.FIELD_WEB_LINK2]

        # Populate minors
        for index in range(9, 14):
            name = row[FamilyRecord.HEADER[index]]
            if len(name.strip()) > 0:
                member_entry = membership.get_one_member_by_fullname(name, True)
                if member_entry is not None:
                    record.minors.append(member_entry)
                else:
                    print(f"Warning: minor in family record not found {name}")

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
                if adult.name.fullname().lower() == name.lower():
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
 
class MemberRecord:
    """
    Reports the waiver status details for any type of member waiver request
    Family or adult. Reporting only
    """

    def __init__(self) -> None: 
        self.adults: list[MemberEntry] = []
        self.signatures: list[bool] = [False, False].copy()
        self.minors: list[MemberEntry] = []
        self.signed: bool = False
        self.has_key: bool = False
        self.key_enabled: bool = False
        self.web_links: list[str] = ["", ""].copy()

    def rank(self) -> int:
        """
        Return a rank value for the record to use in sorting.
        Sort order:
            1 - unsigned, has key, key enabled
            2 - signed, has key, key not enabled
            3 - unsinged, has key, key not enabled
            4 - signed, has key, key enabled
            5 - unsigned, any, any
            6 - signed, any, any
        """
        if not self.signed:
            if self.has_key:
                if self.key_enabled:
                    return 1
                else:
                    return 3
            else:
                return 5
        else:
            if self.has_key:
                if self.key_enabled:
                    return 4
                else:
                    return 2
            else:
                return 6
            
    FIELD_NAME1 ="name1"
    FIELD_SIGNATURE1 = "signed1"
    FIELD_WEB_LINK1 = "web_link1"
    FIELD_NAME2 ="name2"
    FIELD_SIGNATURE2 = "signed2"
    FIELD_WEB_LINK2 = "web_link2"

    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_MINOR5 = "minor5"

    FIELD_HAS_KEY = "has_key"
    FIELD_KEY_ENABLED = "key_enabled"

    HEADER =[ csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, csvfile.SIGNED, FIELD_HAS_KEY, FIELD_KEY_ENABLED,
           FIELD_NAME1, FIELD_SIGNATURE1, FIELD_NAME2, FIELD_SIGNATURE2,
           FIELD_MINOR1, FIELD_MINOR2,
           FIELD_MINOR3, FIELD_MINOR4,  FIELD_MINOR5, FIELD_WEB_LINK1, FIELD_WEB_LINK2 ]

    @staticmethod
    def get_header() -> list[str]:
        return MemberRecord.HEADER
   
    def get_row(self):
        row = {}
        if len(self.adults) == 0:
            return row

        row[csvfile.ACCOUNT_NUM] = self.adults[0].account_num
        row[csvfile.MEMBER_ID] = self.adults[0].member_id
        row[csvfile.SIGNED] = "signed" if self.signed else ""
        row[MemberRecord.FIELD_HAS_KEY] = "has key" if self.has_key else ""
        row[MemberRecord.FIELD_KEY_ENABLED] = "enabled" if self.key_enabled else ""

        row[MemberRecord.FIELD_NAME1] = self.adults[0].name.fullname()
        row[MemberRecord.FIELD_SIGNATURE1] = "signed" if self.signatures[0] else ""
        row[MemberRecord.FIELD_WEB_LINK1] = self.web_links[0]

        if len(self.adults) > 1:
            row[MemberRecord.FIELD_NAME2] = self.adults[1].name.fullname()
            row[MemberRecord.FIELD_SIGNATURE2] = "signed" if self.signatures[1] else ""
            row[MemberRecord.FIELD_WEB_LINK2] = self.web_links[1]

        for i, minor in enumerate(self.minors):
            row[MemberRecord.HEADER[i + 9]] = minor.name.fullname()
        return row

    def get_account_num(self) -> str:
        if len(self.adults) > 0:
            return self.adults[0].account_num
        return "0"

    def get_member_id(self) -> str:
        if len(self.adults) > 0:
            return self.adults[0].member_id
        return "0"

    def has_minors(self) -> bool:
        return len(self.minors) > 0

    def get_member_ids(self) -> list[str]:
        ids: list[str] = []
        for adult_record in self.adults:
            ids.append(adult_record.member_id)
        for minor_record in self.minors:
            ids.append(minor_record.member_id)
        return ids

    @staticmethod
    def key_func(record: MemberRecord) -> tuple[int, int, bool, int]:
        return (record.rank(), int(record.get_account_num()), not record.has_minors(), int(record.get_member_id()))

    @staticmethod
    def write_csv(records: list[MemberRecord], csv_file: str) -> None:
        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: Write {csv_file}")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=MemberRecord.get_header())
            writer.writeheader()
            for record in records:
                writer.writerow(record.get_row())
            f.close()

    member_csv = "output/member_records.csv"

    @staticmethod
    def gen_records(groups: MemberWaiverGroups, member_keys: dict[str,keys.KeyEntry]) -> list[MemberRecord]:
        """
        """
        member_records: list[MemberRecord] = []

        for adult_record in groups.no_minor_children:
            member_record = MemberRecord()
            member_record.adults.append(adult_record.member)
            member_record.web_links[0] = adult_record.web_link
            member_record.signed = adult_record.signed
            member_record.signatures[0] = adult_record.signed
            for member_id in member_record.get_member_ids():
                if member_id in member_keys:
                    member_record.has_key = True
                    member_record.key_enabled = member_keys[member_id].enabled
            member_records.append(member_record)

        for family_record in groups.with_minor_children:
            member_record = MemberRecord()
            member_record.adults = family_record.adults.copy()
            member_record.minors = family_record.minors.copy()
            member_record.signed = family_record.signed
            member_record.signatures = family_record.signatures.copy()
            member_record.web_links = family_record.web_links.copy()

            for member_id in member_record.get_member_ids():
                if member_id in member_keys:
                    member_record.has_key = True
                    if member_keys[member_id].enabled:
                        member_record.key_enabled = True
            member_records.append(member_record)

        for family_record in groups.unknown_status:
            member_record = MemberRecord()
            member_record.adults = family_record.adults.copy()
            member_record.minors = family_record.minors.copy()
            for member_id in member_record.get_member_ids():
                if member_id in member_keys:
                    member_record.has_key = True
                    if member_keys[member_id].enabled:
                        member_record.key_enabled = True
 
            member_records.append(member_record)

        member_records.sort(key=MemberRecord.key_func)
        return member_records



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

    groups = MemberWaiverGroups()
    groups.no_minor_children = adult_records
    groups.with_minor_children = family_records
    member_records: list[MemberRecord] = MemberRecord.gen_records(groups, member_keys)
    member_csv = "test/member_records.csv"
    MemberRecord.write_csv(member_records, member_csv)

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
    

