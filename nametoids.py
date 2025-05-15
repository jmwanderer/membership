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
    """
    Read first name, last name columns and return a list of MemberName
    """
    result = []
    count = 0
    reader = csv.DictReader(stream)
    for row in reader:
        if len(row[fn_col]) > 0 or len(row[ln_col]) > 0:
            count += 1
            result.append(memberdata.MemberName(row[fn_col], row[ln_col]))
    print(f"Note: read {len(result)} rows")
    return result

def read_full_name_columns(stream: io.TextIOBase, columns: list[str]) -> list[str]:
    """
    Read one or more full name columns and return a list of strings
    """
    result = []
    count = 0
    reader = csv.DictReader(stream) 
    for row in reader:
        count += 1
        for column in columns:
            if len(row[column]) > 0:
                result.append(row[column])

    print(f"Note: read {len(result)} entries from {count} records")
    return result


def lookup_ids_member_names(membership: memberdata.Membership,
                            member_names: list[memberdata.MemberName]) -> tuple[list[str], list[str]]:
    account_ids: list[str] = []
    member_ids: list[str] = []

    for name in member_names:
        members = membership.find_members_by_name(name)
        if len(members) == 0:
            print(f"Warning: could not find a member record matching {name}")
        elif len(members) > 1:
            print(f"Warning: found {len(members)} records matching {name}")

        for member in members:
            if member.account_num not in account_ids:
                account_ids.append(member.account_num)
            if member.member_id not in member_ids:
                member_ids.append(member.member_id)

    print(f"Lookup {len(account_ids)} unique accounts and {len(member_ids)} members from {len(member_names)} records.")
    return account_ids, member_ids

def lookup_ids_fullnames(membership: memberdata.Membership,
                         fullnames: list[str]) -> tuple[list[str], list[str]]:
    account_ids: list[str] = []
    member_ids: list[str] = []

    for name in fullnames:
        members: list[memberdata.MemberEntry] = membership.get_members_by_fullname(name)

        if len(members) == 0:
            print(f"Warning: could not find a member record matching {name}")
        elif len(members) > 1:
            print(f"Warning: found {len(members)} records matching {name}")

        for member in members:
            if member.account_num not in account_ids:
                account_ids.append(member.account_num)
            if member.member_id not in member_ids:
                member_ids.append(member.member_id)

    print(f"Lookup {len(account_ids)} unique accounts and {len(member_ids)} members from {len(fullnames)} names.")
    return account_ids, member_ids

        
def write_ids(account_ids: list[str], member_ids: list[str]):
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


def main(input_source):
    input_filename = input_source[0]
    fullnames = input_source[1]
    column_names = input_source[2]

    input_file = open(input_filename, newline="")
    print(f"Note: reading names from '{input_filename}'")
    if fullnames:
        names = read_full_name_columns(input_file, column_names)
    else:
        member_names = read_name_columns(input_file, column_names[0], column_names[1])
    input_file.close()
    print("")

    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()
    print("")

    print("Looking up member names...")
    if fullnames:
        account_ids, member_ids = lookup_ids_fullnames(membership, names)
    else:
        account_ids, member_ids = lookup_ids_member_names(membership, member_names)

    write_ids(account_ids, member_ids)


INPUTS = { "swimteam": ("input/swim_team.csv", False, ( "First Name", "Last Name")),
           "waivers": ("output/member_waivers.csv", True, ("signer1", "signer2", "signer3", "signer4", "minor1", "minor2", "minor3", "minor4" )) }

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in INPUTS:
        print(f"Usage: {sys.argv[0]} <input source>")
        sources = [ i for i in INPUTS.keys() ]
        print(f"Sources: {', '.join(sources)}")
        sys.exit(-1)
    main(INPUTS[sys.argv[1]])
    
    

 
