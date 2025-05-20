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


### Generate Waiver Signing Groups

- adults with no minor children
- parents with minor children

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

### extract_attest.py

Extract information from signed PDF documents in the 2025 Household Attestations and Household Waiver files

Note: need credentials.json to access gdrive data
See: https://developers.google.com/workspace/drive/api/quickstart/python

### extract_members.py

Extract information from signed PDF documents in the 2025 Member Waivers folder.
Note: need credentials.json to access gdrive data

### extract_guests.py

Extract information from signed PDF documents in the 2025 Guest Waivers folder.
Note: need credentials.json to access gdrive data

### review_attestations.py

Compare attestations.csv (built with extract_attest.py) with member data in the member.csv and account.csv
files. 

## TODO
- Download status files from gdrive automatically: 
https://devnodes.in/blog/web/python-export-google-sheet-to-csv/. Try files.export: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/export

### selectids.py

Read names or ids from a CSV and lookup matching members. Write member ids and account ids to temp files to use in updating another file

### updaterows.py

Mark or clear a file in rows that match member ids or account ids saved by selectids.py
Rewrites existing file, backup old file to: <name>.<num>.csv where num is 1, 2, 3, ...
