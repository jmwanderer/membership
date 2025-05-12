"""
Lookup account and member IDs from member names in CSV files.
Write:
    - output/member_ids.csv
    - output/account_ids.csv
to be used by updaterows.py
"""

import csv
import io
import sys
import memberdata

def read_name_columns(stream: io.TextIOBase, fn_col: str, ln_col: str) -> list[memberdata.MemberName]:
    print(f"Note: reading CSV from stdin...")
    result = []
    count = 0
    reader = csv.DictReader(stream)
    for row in reader:
        count += 1
        if count == 1:
            continue
        result.append(memberdata.MemberName(row[fn_col], row[ln_col]))
    print(f"Note: read {len(result)} rows")
    return result

def lookup_ids(membership: memberdata.Membership,
               member_names: list[memberdata.MemberName]) -> tuple[list[str], list[str]]:
    account_ids: list[str] = []
    member_ids: list[str] = []

    for name in member_names:
        members = membership.find_members_by_name(name)
        if len(members) != 1:
            print(f"Warning: found {len(members)} records matching {name}")
            continue
        if members[0].account_num not in account_ids:
            account_ids.append(members[0].account_num)
        if members[0].member_id not in member_ids:
            member_ids.append(members[0].member_id)
    print(f"Lookup {len(account_ids)} unique accounts and {len(member_ids)} members from {len(member_names)} records.")
    return account_ids, member_ids
        
        

def main(input_filename: str):
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    ln_col = "Last Name"
    fn_col = "First Name"

    input_file = open(input_filename, newline="")
    member_names = read_name_columns(input_file, fn_col, ln_col)
    account_ids, member_ids = lookup_ids(membership, member_names)
    input_file.close()

    # Write account ids
    accounts_filename = "output/account_ids.csv"
    output_file = open(accounts_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow([ "Account#" ])
    for entry in account_ids:
        output_csv.writerow([ entry ])
    output_file.close()
    print(f"Note: wrote {accounts_filename}")

    # Write member ids
    members_filename = "output/member_ids.csv"
    output_file = open(members_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow([ "Member ID" ])
    for entry in member_ids:
        output_csv.writerow([ entry ])
    output_file.close()
    print(f"Note: wrote {members_filename}")



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input file>")
        sys.exit(-1)
    main(sys.argv[1])
    
    

 