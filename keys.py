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
updated_keys_filename = "output/credential_update.csv"

@dataclass
class KeyEntry:
    """Reprents a user key record"""
    member_name: memberdata.MemberName
    account_num: str
    member_email: str
    enabled: bool
    member_id: str = ""
    key_id: str = ""

    def is_staff(self) -> bool:
        return self.account_num.lower().startswith("staff")

    def has_id(self) -> bool:
        return len(self.member_id) > 0


class MemberKeys:
    """Set of keys held by members"""
    def __init__(self) -> None:
        self.member_key_map: dict[str, KeyEntry] = {}
        self.key_entry_list: list[KeyEntry] = []

    def load_keys(self, membership: memberdata.Membership):
        self.key_entry_list = read_key_entries()
        self.member_key_map = gen_member_key_map(membership, self.key_entry_list)

    def has_key(self, member_id: str) -> bool:
        return member_id in self.member_key_map
    
    def has_enabled_key(self, member_id: str) -> bool:
        return self.has_key(member_id) and self.member_key_map[member_id].enabled

    def member_email(self, member_id: str) -> str:
        key_entry = self.member_key_map.get(member_id)
        if key_entry is not None:
            return key_entry.member_email
        return ""

    def key_entries(self) -> list[KeyEntry]:
        return self.key_entry_list



def read_key_file(filename=keys_filename) -> list[dict[str,str]]:
    if not os.path.exists(filename):
        print(f"Note: no filename {filename}")
        return  []

    key_file = open(filename, newline="", encoding="utf-8-sig")
    reader = csv.DictReader(key_file)
    rows = list(reader)
    key_file.close()
    return rows

def write_key_file(filename: str, rows: list[dict[str,str]]):
    # Assume at least one element
    fieldnames = rows[0].keys()
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()

FORCE_UPDATE = "ForceUpdate"
FIRST_NAME = "FirstName"
LAST_NAME = "LastName"
USER_NAME = "UserName"
EMAIL = "Email"
EXTERNAL_ID = "ExternalId"
EXPIRATION = "CredentialExpirationDateTime"
REMOVE_USER = "RemoveUser"
CREDENTIAL_STATUS = "CredentialStatus"
ACTIVE = "Active"
INACTIVE = "Deactivated"
MOBILE_ENABLED = "EnableMobileCredential"

def read_key_entries(filename=keys_filename) -> list[KeyEntry]:
    """
    Read the CSV file and return a list of key entry records
    """
    # Read mobile key information
    key_entry_list: list[KeyEntry] = []
    print(f"Loading mobile keyfile: {filename}")

    rows = read_key_file(filename)
    if rows is None:
        print(f"Note: no filename {filename}")
        return key_entry_list


    # Iterate over keys
    for row in rows:
        first_name = row[FIRST_NAME].strip()
        last_name = row[LAST_NAME].strip()
        email = row[EMAIL].strip()
        account_num = row[USER_NAME]
        enabled = row[CREDENTIAL_STATUS] == ACTIVE
        key_id = row[EXTERNAL_ID]

        member_name = memberdata.MemberName(first_name=first_name, last_name=last_name)
        entry = KeyEntry(
            member_name=member_name, account_num=account_num, member_email=email, enabled=enabled,
            key_id=key_id
        )
        key_entry_list.append(entry)

    return key_entry_list

   
 
#### TODO::: IN PROGRESS -- develop a set of keys that include no members

def gen_member_key_map(membership: memberdata.Membership,
                       key_entries: list[KeyEntry]) -> dict[str, KeyEntry]:
    """
    Generate a dictionary mapping member ids to KeyEntries
    Used to find key information for a specific member
    """
    member_key_map = {}

    for key_entry in key_entries:
        if key_entry.is_staff():
            continue

        members = membership.find_members_by_name(key_entry.member_name)
        if len(members) == 0:
            print(f"Warning: no members found for key file name {key_entry.member_name}")
            continue
        elif len(members) > 1:
            print(f"Warning: muiltiple members found for key file name {key_entry.member_name}")

        member = members[0]
        key_entry.member_id = member.member_id
        if member.account_num != key_entry.account_num:
            print(
                f"Warning: key and member account numbers don't match key file name for {key_entry.member_name}"
            )
        member_key_map[member.member_id] = key_entry
    return member_key_map


def simple_test():
    membership = memberdata.Membership()
    membership.read_csv_files()

    key_map = gen_member_key_map(membership, read_key_entries())

    member_keys = MemberKeys()
    member_keys.load_keys(membership)
    member_keys.has_enabled_key("0")


if __name__ == "__main__":
    simple_test()
