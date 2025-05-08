# Club Membership Tools
Scripts for working with membership data tracked in CSV files

## Input Files
Scripts read input from input/

- members.csv : export member list with email addresses
- accounts.csv : export account list 
- keys.csv : key entries

## Tools

### Review Account Keys

Generate report of number of keys held by each member account.
Report discrepencies between keys file and member data.

Useful to find who does not have keys and find keys that are assigned
to non-members.

Ignores keys with user names that start with "Staff..."

review_account_keys.py

Output:
- account_keys.csv: list of member accounts and number of keys held


### Generate Parent List

Generate a CSV of accounts with minor children and guess which
adults are the parents based on ages. Will leave parents blank if
unsure to be manuall updated.

gen_parent_list.py

Output:
- parent_list.csv - list of families, parents and minor children

### Key Email Delta

Find members that have an email address for a mobile key that do not
have an email in the membership database.

key_email_delta.py

Output:
- new_email.csv: members that need an email added to the member database
- change_email.csv: notes that email in the member database is different than the key

### extract_attestation.py

Extract information from signed PDF documents in the 2025 Household Attestations and Household Waiver files

Note: need credentials.json to access gdrive data
See: https://developers.google.com/workspace/drive/api/quickstart/python


