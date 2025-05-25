"""
Utility functions and common constants for working with CSV files

TODO:
  - consider creating a base class for records stored as CSV rows
"""

import re
import os


def get_backup_filename(filename: str) -> str | None:
    """
    Search for a backup filename not in use
    """
    m = re.match(r"(.+)\.csv", filename)
    if m is None:
        return None
    prefix = m.group(1)
    value = 1
    # Avoid an infinite loop in a hypothetical pathalogical case.
    while value < 10000:
        backup_name = f"{prefix}.{value}.csv"
        if not os.path.exists(backup_name):
            return backup_name
        value += 1
    return None


def backup_file(filename: str) -> bool:
    """
    Rename a CSV file to save as a backup
    """
    backup_name = get_backup_filename(filename)
    if backup_name is None:
        print(f"Error: file must be <name>.csv")
        return False
    if os.path.exists(filename):
        #print(f"Note: moving '{filename}' to '{backup_name}'")
        os.rename(filename, backup_name)
    return True

def is_signed(field_val: str) -> bool:
    return len(field_val) > 0 and field_val.lower()[0] == 'y'

def signed_str(signed: bool) -> str:
    if signed:
        return "yes"
    return "no"


ACCOUNT_NUM = "Account#"
MEMBER_ID = "Member#"
SIGNED = "signed"
