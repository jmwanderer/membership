"""
Read the mobile key CSV file
"""

import csv
import os
from dataclasses import dataclass

import memberdata
import csvfile


# Input file
keys_filename = "input/keys.csv"


@dataclass
class KeyEntry:
    """Reprents a user key record"""

    member_name: memberdata.MemberName
    account_num: str
    member_email: str
    enabled: bool

class MemberKeys:
    """Set of keys held by members"""
    def __init__(self):
        self.member_key_map: dict[str, KeyEntry] = {}

    def load_keys(self, membership: memberdata.Membership):
        self.member_key_map = gen_member_key_map(membership)

    def has_key(self, member_id: str) -> bool:
        return member_id in self.member_key_map
    
    def has_enabled_key(self, member_id: str) -> bool:
        return self.has_key(member_id) and self.member_key_map[member_id].enabled


def read_key_entries(filename=keys_filename) -> list[KeyEntry]:
    """
    Read the CSV file and return a list of key entry records
    """
    # Read mobile key information
    key_entry_list: list[KeyEntry] = []
    print(f"Loading mobile keyfile: {filename}")

    if not os.path.exists(filename):
        print(f"Note: no filename {filename}")
        return key_entry_list

    key_file = open(filename, newline="", encoding="utf-8-sig")
    reader = csv.DictReader(key_file)


    # Iterate over keys
    for row in reader:
        first_name = row["FirstName"].strip()
        last_name = row["LastName"].strip()
        email = row["Email"].strip()
        account_num = row["UserName"]
        enabled = csvfile.is_true_value(row["EnableMobileCredential"])

        member_name = memberdata.MemberName(first_name=first_name, last_name=last_name)
        entry = KeyEntry(
            member_name=member_name, account_num=account_num, member_email=email, enabled=enabled
        )
        key_entry_list.append(entry)

    key_file.close()

    return key_entry_list


def gen_member_key_map(membership: memberdata.Membership) -> dict[str, KeyEntry]:
    """
    Generate a dictionary mapping member ids to KeyEntries
    Used to find key information for a specific member
    """
    member_key_map = {}

    for key_entry in read_key_entries():
        if key_entry.account_num.lower().startswith("staff"):
            continue
        members = membership.find_members_by_name(key_entry.member_name)
        if len(members) == 0:
            print(f"Warning: no members found for name {key_entry.member_name}")
            continue
        elif len(members) > 1:
            print(f"Warning: muiltiple members found for name {key_entry.member_name}")
        member = members[0]
        if member.account_num != key_entry.account_num:
            print(
                f"Warning: key and member account numbers don't match for {key_entry.member_name}"
            )
        member_key_map[member.member_id] = key_entry
    return member_key_map




def simple_test():
    membership = memberdata.Membership()
    membership.read_csv_files()

    key_map = gen_member_key_map(membership)

    member_keys = MemberKeys()
    member_keys.load_keys(membership)
    member_keys.has_enabled_key("0")


if __name__ == "__main__":
    simple_test()
