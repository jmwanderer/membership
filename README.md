# Club Membership Tools
Scripts for working with membership data tracked in CSV files

## Input Files
Scripts read input from input/

- members.csv : export member list with email addresses
- accounts.csv : export account list 
- keys.csv : Key entries

## Tools

### Review Account Keys

Generate report of number of keys held by each member account.
Report discrepencies between kes yfile and member data.
Verifies that keyholders have signed the waiver and are current on dues
Useful to find who does not have keys.

Ignores keys with user names that start with "Staff..."

review_account_keys.py

Output:
- account_keys.csv: list of member accounts and number of keys helpd


### Generate Parent List

Generate a CSV of accounts with minor children and guess which
adults are the parents based on ages. Will leave parents blank if
unsure to be manuall updated.

gen_parent_list.py

Output:
- parent_list.csv

### Key Email Delta

Find members that have an email address for a mobile key that do not
have an email in the membership database.

key_email_delta.py

Output:
- new_email.csv: members that need an email added to the member database
- change_email.csv: notes that email in the member database is different than the key


