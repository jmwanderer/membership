# Club Membership Tools
Scripts for working with membership data tracked in CSV files

## Input Files
The scripts read data located in the directory: *input*

To setup, exporting data in CSV format for members and accounts. Apply a filter for members to include the birthday.

Files:
- members.csv : export member list with email addresses
- accounts.csv : export account list 
- parents.csv : (optional) information about who are the parents for specific children
- keys.csv : (optional) key entries


## Tools

There are tools to extract information from PDFs, generate CSVs for waiver signing requests,
reviewing yes, and making ad-hoc queriies

*Backup Files:*
Note, when files are rewritten, generally the existing file s moved to: <name>.<num>.csv where num is 1, 2, 3, ...

### Extract Information from PDFs
Download files from Google Drive and extract information

Note: need credentials.json to access gdrive data
See: https://developers.google.com/workspace/drive/api/quickstart/python

The extract scripts skip files that have already been parsed.

Extract scripts:
  - extract member waivers: extract_members.py - writes to output/member_waivers.csv
  - extract member attestations: extract_attestations.py - writes to output/attestations.csv
  - extract guest waivers: extract_guest.py - writes to output/guest_waivers.csv

### Generate CSV Files

Script that create specific CSV files:

#### Report stats on waivered members

file: waiver_calcs.py


#### Generate Groups for Signature Request 

file: gen_waiver_groups.py

Generate a CSV of adult accounts and accounts with minor children.
If there are multiple adults, guess which adults are the parents based on ages.
If unable to guess, write to the unkown list.

Generate CSV for bulk signature requests:
- adult waivers: adults_records.csv
- familiy waivers with two parents and minors listed: family_records.csv
- unknown families, needs resolution in input/parents.csv: unknown_familes.csv

#### Compile Information for Keys

Useful to find who does not have keys and find keys that are assigned
to non-members and to update the member database with new email addresses.

  - review_account_keys.py: Look for mis-assigned keys
    - create output/account_keys.csv: list of member accounts and number of keys held
    - Ignores keys with user names that start with "Staff..."
  - key_email_delta: find emails in key file not in member file. Creates *output/*
      - new_email.csv : email addresses for members that have no email
      - change_email.csv : email addresses that a different than the member file

#### Review Data from Attestations

file: review_attestations.py

Find discrepancies between the member database and information in attestion PDF files

#### AdHoc Queries

To avoid writing a custom function for any type of data analysis, AdHoc queries support
selecting members and accounts matching specific pre-defined criteria (e.g. have signed a waiver)
with selectids.py and then updating columns in CSV files in rows that match the selected members
and accounts.

In addition to the pre-configured queries (see below), selectids.py can also read the following
data:
- fullnames
- first name, last name
- member id or account id


##### selectids.py

Runs pre-configured queries against CSV files in the *input/* and *output/* directories.
Resolves names in the files to member ids, and saves member ids and account ids for use by updaterows.py

Available Queries:
- attest_signer: members that signed attestations
- keys: members / accounts holding keys
- swimteam: members on swimteam / accounts with swimmers on the swimteam
- ids: load Member# or Account# from output/ids.csv
- fullnames: load name from output/fullnames.csv
- names: load First Name and Last Name from output/names.csv


Potential bug: reporting family waiver status for one household with multiple families (sets of parents and children)


##### updaterows.py

Mark or clear a specified column in rows that match member ids or account ids loaded by selectids.py


## How To

