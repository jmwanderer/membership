"""
Read mobile key entries
"""

import csv
from dataclasses import dataclass

import memberdata


# Input file
keys_filename = "input/keys.csv"


@dataclass
class KeyEntry:
    """Reprents a user key record"""

    member_name: memberdata.MemberName
    account_num: str
    member_email: str


def read_key_entries(filename=keys_filename) -> list[KeyEntry]:
    # Read mobile key information
    print(f"Loading mobile keyfile: {filename}")
    key_file = open(filename, newline="", encoding="utf-8-sig")
    reader = csv.DictReader(key_file)

    key_entry_list = []

    # Iterate over keys
    for row in reader:
        first_name = row["First Name"].strip()
        last_name = row["Last Name"].strip()
        email = row["Email"].strip()
        account_num = row["UserName"]

        member_name = memberdata.MemberName(first_name=first_name, last_name=last_name)
        entry = KeyEntry(
            member_name=member_name, account_num=account_num, member_email=email
        )
        key_entry_list.append(entry)

    key_file.close()

    return key_entry_list

def gen_member_key_map(membership: memberdata.Membership) -> dict[str,KeyEntry]:
    """
    Generate a dictionary mapping member ids to KeyEntries
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
            print(f"Warning: key and member account numbers don't match for {key_entry.member_name}")
        member_key_map[member.member_id] = key_entry
    return member_key_map

def simple_test():
    membership = memberdata.Membership()
    membership.read_csv_files()

    member_keys = gen_member_key_map(membership)

if __name__ == "__main__":
    simple_test()
        

        