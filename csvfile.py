"""
Utility functions and common constants for working with CSV files

TODO:
  - consider creating a base class for records stored as CSV rows
"""

import re
import os


def get_backup_filenames(filename: str) -> list[str]:
    """
    Search for a backup filename not in use
    """
    m = re.match(r"(.+)\.csv", filename)
    if m is None:
        return []
    prefix = m.group(1)
    result = []
    result.append(f"{prefix}.bck1.csv")
    result.append(f"{prefix}.bck2.csv")
    return result

def backup_file(filename: str) -> bool:
    """
    Rename a CSV file to save as a backup
    """
    backup_names = get_backup_filenames(filename)
    if len(backup_names) == 0:
        print(f"Error: file must be <name>.csv")
        return False

    # unlink bck2
    if os.path.exists(backup_names[1]):
        os.unlink(backup_names[1])
    # mv bck1 to bck2
    if os.path.exists(backup_names[0]):
        os.rename(backup_names[0], backup_names[1])
    # mv filename to bck1
    if os.path.exists(filename):
        #print(f"Note: moving '{filename}' to '{backup_name}'")
        os.rename(filename, backup_names[0])
    return True

def is_signed(field_val: str) -> bool:
    return len(field_val) > 0 and field_val.lower()[0] == 'y'

def signed_str(signed: bool) -> str:
    if signed:
        return "yes"
    return "no"

def is_true_value(field_val: str) -> bool:
    field_val = field_val.strip()
    return len(field_val) > 0 and (field_val.lower()[0] == 't' or field_val.lower()[0] == 'y')

def bool_str(value: bool) -> str:
    if value:
        return "yes"
    else:
        return ""

ACCOUNT_NUM = "Account#"
MEMBER_ID = "Member#"
SIGNED = "signed"
