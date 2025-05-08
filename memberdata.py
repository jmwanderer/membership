"""
Access Membership accounts and members via exported CSV files
"""

import csv
import datetime
from dataclasses import dataclass
from collections.abc import Iterator
import sys

# Default filenames for CSVs
MEMBERS_CSV = "input/members.csv"
MEMBERS_TEST_1_CSV = "test/members.test1.csv"
MEMBERS_TEST_2_CSV = "test/members.test2.csv"
ACCOUNTS_CSV = "input/accounts.csv"
ACCOUNTS_TEST_CSV = "test/accounts.test.csv"


@dataclass
class MemberName:
    """First and last name"""

    first_name: str
    last_name: str

    def fullname(self):
        return f"{self.first_name} {self.last_name}"

    def __eq__(self, other):
        return self.first_name == other.first_name and self.last_name == other.last_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.first_name, self.last_name))

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


@dataclass
class MemberEntry:
    """Represents the data for a specific club member"""

    name: MemberName
    account_num: str
    member_id: str
    member_type: str
    email: str
    birthdate: datetime.date

    def has_birthdate(self) -> bool:
        age = self.age()
        return age >= 0 and age < 110

    def is_child_type(self) -> bool:
        return self.member_type == "Child"

    def is_adult_type(self) -> bool:
        return self.member_type == "Adult"

    def age(self) -> int:
        today = datetime.date.today()
        years = today.year - self.birthdate.year
        birthday = self.birthdate.replace(year=today.year)
        if birthday > today:
            years -= 1
        return years

    def is_minor(self):
        return (self.has_birthdate() and self.age() < 18) or (
            not self.has_birthdate() and self.is_child_type()
        )

    """Column names for member entries"""
    FIELD_ACCOUNT_NUM = "Acct #"
    FIELD_MEMBER_ID = "Member ID"
    FIELD_MEMBER_TYPE = "Member Type"
    FIELD_FIRST_NAME = "First Name"
    FIELD_LAST_NAME = "Last Name"
    FIELD_EMAIL = "Email"
    FIELD_BIRTHDATE = "Birthdate"


@dataclass
class AccountEntry:
    """Represents a club account"""

    account_num: str
    account_type: str
    billing_name: MemberName
    email: str

    def is_proprietary_member(self) -> bool:
        return self.account_type == "Proprietary Member Annual"

    def is_staff(self) -> bool:
        return self.account_type == "Staff"

    """Column names for member accounts"""
    FIELD_ACCOUNT_NUM = "Acct #"
    FIELD_ACCOUNT_TYPE = "Acct Type"
    FIELD_FIRST_NAME = "First Name"
    FIELD_LAST_NAME = "Last Name"
    FIELD_EMAIL = "Email"
    FIELD_STREET_ADDRESS = "Street Address"

    ACTIVE_ACCOUNT_TYPES = [
        "Proprietary Member Annual",
        "Staff",
        "Special Leave with Alumni Passes",
    ]


class Membership:
    """Account and member entries"""

    def __init__(self) -> None:
        self.member_map: dict[MemberName, list[MemberEntry]] = {}
        self.member_name_map: dict[str, list[MemberEntry]] = {}
        self.account_map: dict[str, AccountEntry] = {}

    def read_csv_files(self, accounts_file=ACCOUNTS_CSV, members_file=MEMBERS_CSV):
        """
        Read account and member CSV files.
        """
        self._read_accounts_csv(accounts_file)
        self._read_members_csv(members_file)

    def member_names(self) -> list[MemberName]:
        result: list[MemberName]
        result = list(self.member_map.keys())
        return result

    def account_nums(self) -> list[str]:
        result: list[str]
        result = list(self.account_map.keys())
        return result

    def get_members_by_name(self, member_name: MemberName) -> list[MemberEntry]:
        return self.member_map[member_name]

    def get_members_by_fullname(self, member_name: str) -> list[MemberEntry]:
        return self.member_name_map[member_name.lower()]

    def accounts(self) -> list[AccountEntry]:
        result: list[AccountEntry]
        result = list(self.account_map.values())
        return result

    def get_account_by_fullname(self, fullname) -> AccountEntry | None:
        members = self.member_name_map.get(fullname.lower())
        if members is None or len(members) == 0:
            return None

        account_num = None
        for member in members:
            if account_num == None:
                account_num = member.account_num
            else:
                if account_num != member.account_num:
                    print("Error: multiple accounts for {fullname}")
        return self.account_map[account_num]
            
    def get_members_for_account_num(self, account_num: str) -> list[MemberEntry]:
        if account_num not in self.account_map:
            print("Warning: Account {account_num} does not exist.")
            return []

        result = []
        for member in self.all_members():
            if member.account_num == account_num:
                result.append(member)
        return result

    def all_members(self) -> Iterator[MemberEntry]:
        for entries in self.member_map.values():
            for entry in entries:
                yield entry

    def get_account(self, account_num: str) -> AccountEntry:
        return self.account_map[account_num]

    def _read_members_csv(self, filename):
        print(f"Note: reading member list '{filename}'")
        self.member_map = {}
        self.member_name_map = {}
        count = 0
        with open(filename, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                count += 1
                account_num = row[MemberEntry.FIELD_ACCOUNT_NUM].strip()
                name = MemberName(
                    row[MemberEntry.FIELD_FIRST_NAME].strip(),
                    row[MemberEntry.FIELD_LAST_NAME].strip(),
                )

                # Check account is active
                if account_num not in self.account_map:
                    # print(f"Skipping member {name}")
                    continue

                birthdate_str = ""
                if MemberEntry.FIELD_BIRTHDATE in row:
                    birthdate_str = row[MemberEntry.FIELD_BIRTHDATE].strip()
                if birthdate_str == "":
                    birthdate = datetime.date.min
                else:
                    try:
                        birthdate = datetime.date.fromisoformat(birthdate_str)
                    except ValueError as e:
                        print(
                            f"Note: Invalid birthdate for member {name}: {birthdate_str}"
                        )
                        birthdate = datetime.date.min

                member = MemberEntry(
                    name,
                    account_num,
                    row[MemberEntry.FIELD_MEMBER_ID].strip(),
                    row[MemberEntry.FIELD_MEMBER_TYPE].strip(),
                    row[MemberEntry.FIELD_EMAIL].strip(),
                    birthdate,
                )
                if name not in self.member_map:
                    self.member_map[name] = []
                    self.member_name_map[name.fullname().lower()] = []
                self.member_map[name].append(member)
                self.member_name_map[name.fullname().lower()].append(member)

                # Birthday stuff
                # if member.hasBirthdate():
                #    print(f"Member {member.name} born {member.birthdate} age {member.age()}")

        print(f"Note: Read {count} member sheet rows")
        print(f"Note: Loaded {len(self.member_map)} members")

        for entries in self.member_map.values():
            if len(entries) > 1:
                name = entries[0].name
                print(f"Note: multiple entries ({len(entries)}) for {name}")

    def _read_accounts_csv(self, filename: str):
        print(f"Note: reading account list '{filename}'")
        # Build dictionary of { account_num : AccountEntry }
        self.account_map = {}
        count = 0
        with open(filename, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                count += 1
                account_num = row[AccountEntry.FIELD_ACCOUNT_NUM].strip()
                account_type = row[AccountEntry.FIELD_ACCOUNT_TYPE].strip()
                billing_first = row[AccountEntry.FIELD_FIRST_NAME].strip()
                billing_last = row[AccountEntry.FIELD_LAST_NAME].strip()
                billing_email = row[AccountEntry.FIELD_EMAIL].strip()

                if account_type not in AccountEntry.ACTIVE_ACCOUNT_TYPES:
                    # print(f"Skipping account type {account_type} #{account_num}")
                    continue

                entry = AccountEntry(
                    account_num,
                    account_type,
                    MemberName(billing_first, billing_last),
                    billing_email,
                )
                self.account_map[account_num] = entry

        print(f"Note: Read {count} account sheet rows")
        print(f"Note: Loaded {len(self.account_map)} accounts")


if __name__ == "__main__":
    members = Membership()
    members.read_csv_files(ACCOUNTS_TEST_CSV, MEMBERS_TEST_1_CSV)
    members.read_csv_files(ACCOUNTS_TEST_CSV, MEMBERS_TEST_2_CSV)
