#
# Generate a list of email addresses that are associated with keys, but
# not found in the members list.
#
# Input:
#   1. Mobile key list
#   2. Account and member export lists
#

import csv
from dataclasses import dataclass
import sys

import csvfile
import memberdata
import keys

# Filenames
new_output_filename = "output/new_email.csv"
change_output_filename = "output/change_email.csv"


# Read membership data
membership = memberdata.Membership()
membership.read_csv_files()

# Build list of KeyEntry
key_list = keys.read_key_entries()
print(f"Note: Read {len(key_list)} mobile key entries")

# Open file for new emails
new_output_file = open(new_output_filename, "w", newline="")
new_output_csv = csv.writer(new_output_file)
row = [csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, "FirstName", "LastName", "NewEmail"]
new_output_csv.writerow(row)

# Open files for emails that have changed
change_output_file = open(change_output_filename, "w", newline="")
change_output_csv = csv.writer(change_output_file)
row = [
    csvfile.ACCOUNT_NUM,
    csvfile.MEMBER_ID,
    "FirstName",
    "LastName",
    "KeyEmail",
    "MemberEmail",
]
change_output_csv.writerow(row)

# Walk through the key entries, find corresponding member entry
# Check email address, if no match, output an update record
new_email_count = 0
changed_email_count = 0
for key_entry in key_list:

    # Get member entry.
    if key_entry.member_name not in membership.member_names():
        print(
            f"Warning: member entry not found account '{key_entry.account_num}' {key_entry.member_name}"
        )
        continue

    for member_entry in membership.get_members_by_name(key_entry.member_name):
        if member_entry.email.lower() != key_entry.member_email.lower():
            if member_entry.email == "":
                row = [
                    member_entry.account_num,
                    member_entry.member_id,
                    member_entry.name.first_name,
                    member_entry.name.last_name,
                    key_entry.member_email,
                ]
                new_email_count += 1
                new_output_csv.writerow(row)
            else:
                row = [
                    member_entry.account_num,
                    member_entry.member_id,
                    member_entry.name.first_name,
                    member_entry.name.last_name,
                    key_entry.member_email,
                    member_entry.email,
                ]
                changed_email_count += 1
                change_output_csv.writerow(row)

print("\n")
print("Checked mobile key email addresses against Member email addresses.")
print(
    f"Created new emails file '{new_output_filename}' with {new_email_count} entries."
)
print(
    f"Created changed emails file '{change_output_filename}' with {changed_email_count} entries."
)
