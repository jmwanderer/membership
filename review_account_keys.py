"""
Generate list of accounts and number of proxess keys
- acnt# first,last name, billing email

TODO: better handling of staff accounts
"""

import csv
import memberdata
import keys


# File to generate
output_filename = "output/account_keys.csv"


# Read membership data
membership = memberdata.Membership()
membership.read_csv_files()

# Map { account_num, key_count }
account_key_count = {}

# Read mobile key information
# Iterate over keys, counting keys
for key_entry in keys.read_key_entries():

    # TODO: consider how staff is modeled in membership database
    if key_entry.account_num.lower().startswith("staff"):
        continue

    if key_entry.account_num not in membership.account_nums():
        print(
            f"Error: Key with invalid account num '{key_entry.account_num}' for {key_entry.member_name}"
        )
        continue
    else:
        account = membership.get_account(key_entry.account_num)
        if not account.is_active_member() and not account.is_staff():
            print(
                f"Error: key held by non-active account {key_entry.member_name} acct# {key_entry.account_num}"
            )

    valid = False
    member_entries = membership.find_members_by_name(key_entry.member_name)
    if len(member_entries) < 1:
        print(
            f"Error: Key with invalid member name {key_entry.member_name} acct# {key_entry.account_num}"
        )
    else:
        for member_entry in member_entries:
            # Find a matching member entry with the same account number
            valid = valid or member_entry.account_num == key_entry.account_num
        if not valid:
            print(
                f"Error: Key account '{key_entry.account_num}' does not match name {key_entry.member_name}"
            )

    if key_entry.account_num not in account_key_count:
        account_key_count[key_entry.account_num] = 0
    account_key_count[key_entry.account_num] += 1


# Open output file
print()
print(f"Creating output file: {output_filename}")
output_file = open(output_filename, "w", newline="")
output_csv = csv.writer(output_file)
output_csv.writerow(["AccountNum", "first_name", "last_name", "email", "key_count"])

account_with_keys_count = 0
account_without_keys_count = 0
max_account_keys = 0
total_keys = 0

for account in membership.accounts():
    key_count = account_key_count.get(account.account_num, 0)
    if account.is_staff():
        # Skip staff accounts
        continue

    if not account.is_proprietary_member():
        # Skip non -proprietary member accounts, but check if there is a key
        if key_count > 0:
            print(
                f"Note: non-proprietary account with keys '{account.account_num}' {account.billing_name}"
            )
        continue

    total_keys += key_count

    if key_count > 0:
        account_with_keys_count += 1
    else:
        account_without_keys_count += 1

    if key_count > max_account_keys:
        max_account_keys = key_count

    output_csv.writerow(
        [
            account.account_num,
            account.billing_name.first_name,
            account.billing_name.last_name,
            account.email,
            key_count,
        ]
    )


output_file.close()

print(f"Total keys: {total_keys}")
print(f"Accounts with keys: {account_with_keys_count}")
print(f"Accounts without keys: {account_without_keys_count}")
print(f"Max keys for an account: {max_account_keys}")
if account_with_keys_count > 0:
    print(
        f"Avg. number of keys for accounts with keys {total_keys / account_with_keys_count}"
    )
