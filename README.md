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

#### Generate list of members with waivers

file: calc_waivered_set.py

Writes output/waivered_members.csv with member names and links to signed waiver documents 

#### Generate Signature Request Groups

file: gen_sign_groups.py

Generate a CSV of adult accounts and accounts with minor children.
If there are multiple adults, guess which adults are the parents based on ages.
If unable to guess, write to the unkown list.

Generate CSV for bulk signature requests:
- adult waivers: adults_no_minor_children.csv
- familiy waivers with two parents and minors listed: parents_to_sign.csv
- unknown families, needs resolution in input/parents.csv: unknown_list_to_sign.csv

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
- waivers: members covered by any type of waiver
- individual_waivers: members covered by an adult individual waivers or attestation signature
- family_waivers: members / accounts covered by family waivers
- family_waivers_incomplete: members that signed family waivers, invalid due to not listing all minors
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

### List waiver status of each member

Ensure output/waivers.csv does not exist.

```
python selectids.py waivers
python updaterows.py member -m waivered output/waivers.csv
```

### Find adult members with keys not yet requested for signatures

There exists a file requests.csv that lists names of all adults that have been asked to sign waivers.
Column name for name column is *name*

Steps:
- start with adults_no_minor_children.csv
- add a column waivered reporting if the member is already covered by a waiber
- add a column has_key reporting if the member has a key
- add a column requested reporting that the member has alreyad been asked for a signature


```
mv requests.csv output/fullnames.csv
python selectids.py waivers
python updaterows.py member -m waivered output/adults_no_minor_children.csv
python selectids.py fullnames
python updaterows.py member -m requested output/adults_no_minor_children.csv
python selectids.py keys
python updaterows.py member -m has_key output/adults_no_minor_children.csv
```

Sort the adult_no_minor_chidren by the waivered, requested, and has_key columns. 

Find the rows with waivered clear, requested clear, but has_key is marked.


### Which families need to sign a family waiver?

Identify accounts with minors that have a key associated with the account but do not yet have a signed family waiver.

```
rm output/families.csv
python selectids.py minors
python updaterows.py account -m minors output/families.csv
python selectids.py keys
python updaterows.py account -m keys output/families.csv
python selectids.py family_waivers
python updaterows.py account -m family_waiver output/families.csv
```

Sort by minors, keys, family_waiver



### Which adults without minor aged children need to sign a waiver?


