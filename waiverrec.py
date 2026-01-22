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


class RequiredWaiver:
    """
    Represents a family or potential family for which we need more information
    """

    def __init__(self, member: MemberEntry|None = None) -> None: 
        self.adults: list[MemberEntry] = []
        self.signatures: list[bool] = [False, False].copy()
        self.web_links: list[str] = ["", ""].copy()
        self.minors: list[MemberEntry] = []
        self.signed: bool = False
        self.has_key: bool = False
        self.key_enabled: bool = False
        if member is not None:
            self.adults.append(member)

    FIELD_HAS_KEY = "has_key"
    FIELD_KEY_ENABLED = "key_enabled"
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
              FIELD_HAS_KEY, FIELD_KEY_ENABLED,
              FIELD_NAME1, FIELD_EMAIL1, FIELD_SIGNATURE1,
              FIELD_NAME2, FIELD_EMAIL2, FIELD_SIGNATURE2,
              FIELD_MINOR1 ,FIELD_MINOR2,
              FIELD_MINOR3, FIELD_MINOR4, FIELD_MINOR5, 
              FIELD_WEB_LINK1, FIELD_WEB_LINK2 ]

    def adult(self) -> MemberEntry:
        return self.adults[0]

    def account_num(self) -> str:
        return self.adult().account_num

    def has_minors(self) -> bool:
        return len(self.minors) > 0

    @staticmethod
    def get_header() -> list[str]:
        return RequiredWaiver.HEADER
   
    def get_row(self):
        row = {}
        if len(self.adults) == 0:
            return row

        row[csvfile.ACCOUNT_NUM] = self.adult().account_num
        row[csvfile.MEMBER_ID] = self.adult().member_id
        row[csvfile.SIGNED] = csvfile.signed_str(self.signed)
        row[RequiredWaiver.FIELD_KEY_ENABLED] = csvfile.bool_str(self.key_enabled)
        row[RequiredWaiver.FIELD_HAS_KEY] = csvfile.bool_str(self.has_key)

        member = self.adult()
        row[RequiredWaiver.FIELD_NAME1] = member.name.fullname()
        row[RequiredWaiver.FIELD_EMAIL1] = member.email
        row[RequiredWaiver.FIELD_SIGNATURE1] = csvfile.signed_str(self.signatures[0])
        row[RequiredWaiver.FIELD_WEB_LINK1] = self.web_links[0]

        if len(self.adults) > 1:
            member = self.adults[1]
            row[RequiredWaiver.FIELD_NAME2] = member.name.fullname()
            row[RequiredWaiver.FIELD_EMAIL2] = member.email
        row[RequiredWaiver.FIELD_SIGNATURE2] = csvfile.signed_str(self.signatures[1])
        row[RequiredWaiver.FIELD_WEB_LINK2] = self.web_links[1]

        for i, minor in enumerate(self.minors):
            row[RequiredWaiver.HEADER[i + 11]] = minor.name.fullname()
        return row

    @staticmethod
    def read_row(membership: memberdata.Membership, row: dict[str, str]) -> RequiredWaiver|None:
        member_id = row[csvfile.MEMBER_ID]
        name = row[RequiredWaiver.FIELD_NAME1]
        member_entry = membership.get_member_by_id(member_id)
        if member_entry is None:
            print(f"Warning: no member id: {member_id} name: '{name}' found.")
            return None


        record = RequiredWaiver()
        record.signed = csvfile.is_signed(row[csvfile.SIGNED])
        record.has_key = csvfile.is_true_value(row[RequiredWaiver.FIELD_HAS_KEY])
        record.key_enabled = csvfile.is_true_value(row[RequiredWaiver.FIELD_KEY_ENABLED])

        # Populate adult 1 plus signature status and web link
        record.adults.append(member_entry)
        record.signatures[0] = csvfile.is_signed(row[RequiredWaiver.FIELD_SIGNATURE1])
        record.web_links[0] = row[RequiredWaiver.FIELD_WEB_LINK1]

        # Populate adult 2 plus signature status and web link
        name = row[RequiredWaiver.FIELD_NAME2]
        if len(name.strip()) > 0:
            member_entry = membership.get_one_member_by_fullname(name, False)
            if member_entry is not None:
                record.adults.append(member_entry)
            else:
                print(f"Warning: member in family record not found {name}")
        record.signatures[1] = csvfile.is_signed(row[RequiredWaiver.FIELD_SIGNATURE2])
        record.web_links[1] = row[RequiredWaiver.FIELD_WEB_LINK2]

        # Populate minors
        for index in range(11, 16):
            name = row[RequiredWaiver.HEADER[index]]
            if len(name.strip()) > 0:
                member_entry = membership.get_one_member_by_fullname(name, True)
                if member_entry is not None:
                    record.minors.append(member_entry)
                else:
                    print(f"Warning: minor in family record not found {name}")

        return record
    
    @staticmethod 
    def read_csv(membership: memberdata.Membership, csv_file: str) -> list[RequiredWaiver]:
        """
        Read CSV file of family waiver records
        """
        result: list[RequiredWaiver] = []

        if not os.path.exists(csv_file):
            return result
        
        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = RequiredWaiver.read_row(membership, row)
                if record is not None:
                    result.append(record)
        return result

    @staticmethod
    def write_csv(records: list[RequiredWaiver], csv_file: str) -> None:
        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: Write {csv_file}")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=RequiredWaiver.get_header())
            writer.writeheader()
            for record in records:
                writer.writerow(record.get_row())
            f.close()
        

class RequiredWaivers:
    """
    Results of generating groupings for member waiver requests
    """

    def __init__(self) -> None:
        # Adult members with no minor children as members
        self.no_minor_children: list[RequiredWaiver] = []

        # Parents and minor children
        self.with_minor_children: list[RequiredWaiver] = []

        # Adults potentially with minor children and minor children
        self.unknown_status: list[RequiredWaiver] = []

        # Statistics for membership
        self.no_minors_count = 0
        self.unknown_parents_count = 0
        self.known_parents_count = 0

    def find_adult_record(self, name: str) -> RequiredWaiver|None:
        for record in self.no_minor_children:
            if record.adult().name.fullname() == name:
                return record
        return None
    
    def find_family_record(self, name: str) -> RequiredWaiver|None:
        for record in self.with_minor_children:
            for adult in record.adults:
                if adult.name.fullname().lower() == name.lower():
                    return record
        return None

    adult_waiver_filename = "output/adult_records.csv"
    familey_waiver_filename = "output/family_records.csv"
    unknown_waiver_filename = "output/unknown_families.csv"

    @staticmethod
    def read_csv_files(membership: memberdata.Membership) -> RequiredWaivers:
        groupings = RequiredWaivers()
        groupings.no_minor_children = RequiredWaiver.read_csv(membership, RequiredWaivers.adult_waiver_filename)
        groupings.with_minor_children = RequiredWaiver.read_csv(membership, RequiredWaivers.familey_waiver_filename)
        groupings.unknown_status = RequiredWaiver.read_csv(membership, RequiredWaivers.unknown_waiver_filename)
        return groupings

    def write_csv_files(self) -> None:
        RequiredWaiver.write_csv(self.no_minor_children, RequiredWaivers.adult_waiver_filename)
        RequiredWaiver.write_csv(self.with_minor_children, RequiredWaivers.familey_waiver_filename)
        RequiredWaiver.write_csv(self.unknown_status, RequiredWaivers.unknown_waiver_filename)
 
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
    def gen_records(required_waivers: RequiredWaivers, member_keys: keys.MemberKeys) -> list[MemberRecord]:
        """
        """
        member_records: list[MemberRecord] = []

        for adult_record in required_waivers.no_minor_children:
            member_record = MemberRecord()
            member_record.adults.append(adult_record.adult())
            member_record.web_links[0] = adult_record.web_links[0]
            member_record.signed = adult_record.signed
            member_record.signatures[0] = adult_record.signed
            member_record.has_key = member_keys.has_key(adult_record.adult().member_id)
            member_record.key_enabled = member_keys.has_enabled_key(adult_record.adult().member_id)
            member_records.append(member_record)

        for family_record in required_waivers.with_minor_children:
            member_record = MemberRecord()
            member_record.adults = family_record.adults.copy()
            member_record.minors = family_record.minors.copy()
            member_record.signed = family_record.signed
            member_record.signatures = family_record.signatures.copy()
            member_record.web_links = family_record.web_links.copy()

            for member_id in member_record.get_member_ids():
                member_record.has_key = member_record.has_key or member_keys.has_key(member_id)
                member_record.key_enabled = member_record.key_enabled or member_keys.has_enabled_key(member_id)
            member_records.append(member_record)

        for family_record in required_waivers.unknown_status:
            member_record = MemberRecord()
            member_record.adults = family_record.adults.copy()
            member_record.minors = family_record.minors.copy()
            for member_id in member_record.get_member_ids():
                member_record.has_key = member_record.has_key or member_keys.has_key(member_id)
                member_record.key_enabled = member_record.key_enabled or member_keys.has_enabled_key(member_id)
            member_records.append(member_record)

        member_records.sort(key=MemberRecord.key_func)
        return member_records



def simple_test() -> None:
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.MemberKeys()
    member_keys.load_keys(membership)

    adult_records: list[RequiredWaiver] = []
    family_records: list[RequiredWaiver] = []

    for account in membership.active_member_accounts():
        members = membership.get_members_for_account_num(account.account_num)
        if membership.has_minor_children(account.account_num):
            family_record = RequiredWaiver()
            for member in members:
                if not member.is_minor():
                    family_record.adults.append(member)
                else:
                    family_record.minors.append(member)
            family_records.append(family_record)
        else:
            for member in members:
                adult_record = RequiredWaiver(member)
                adult_records.append(adult_record)

    required_waivers = RequiredWaivers()
    required_waivers.no_minor_children = adult_records
    required_waivers.with_minor_children = family_records
    member_records: list[MemberRecord] = MemberRecord.gen_records(required_waivers, member_keys)
    member_csv = "test/member_records.csv"
    MemberRecord.write_csv(member_records, member_csv)

    family_csv = "test/family_records.csv"
    adult_csv = "test/adult_records.csv"

    RequiredWaiver.write_csv(family_records, family_csv)
    RequiredWaiver.write_csv(adult_records, adult_csv)

    families = RequiredWaiver.read_csv(membership, family_csv)
    adults = RequiredWaiver.read_csv(membership, adult_csv)

    assert len(families) == len(family_records)
    assert len(adults) == len(adult_records)

    RequiredWaiver.write_csv(families, family_csv)
    RequiredWaiver.write_csv(adults, adult_csv)

    families = RequiredWaiver.read_csv(membership, family_csv)
    adults = RequiredWaiver.read_csv(membership, adult_csv)

    assert len(families) == len(family_records)
    assert len(adults) == len(adult_records)




if __name__ == "__main__":
    simple_test()
    

