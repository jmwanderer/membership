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
        first_name = row["FirstName"].strip()
        last_name = row["LastName"].strip()
        email = row["Email"].strip()
        account_num = row["UserName"]

        member_name = memberdata.MemberName(first_name=first_name, last_name=last_name)
        entry = KeyEntry(
            member_name=member_name, account_num=account_num, member_email=email
        )
        key_entry_list.append(entry)

    key_file.close()

    return key_entry_list
