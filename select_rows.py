"""
Lookup account and member IDs from member names in CSV files.
Write:
    - output/member_ids.csv
    - output/account_ids.csv
to be used by updaterows.py
"""

from dataclasses import dataclass
from typing import Callable
import csv
import io
import sys
import memberdata

def read_name_columns(stream: io.TextIOBase, name_columns: list[tuple[str,str]],
                      cond: Callable[[dict[str,str], str], bool]) -> list[memberdata.MemberName]:
    """
    Read first name, last name columns and return a list of MemberName
    """
    result = []
    count = 0
    fn_col = name_columns[0][0]
    ln_col = name_columns[0][1]
    reader = csv.DictReader(stream)
    for row in reader:
        count += 1
        for fn_col, ln_col in name_columns:
            if len(row[fn_col]) > 0 or len(row[ln_col]) > 0 and cond(row):
                result.append(memberdata.MemberName(row[fn_col], row[ln_col]))
    print(f"Note: read {len(result)} entries from {count} records")
    return result

def read_full_name_columns(stream: io.TextIOBase, columns: list[str],
                           cond: Callable[[dict[str,str], str], bool]) -> list[str]:
    """
    Read one or more full name columns and return a list of strings
    """
    result = []
    count = 0
    reader = csv.DictReader(stream) 
    for row in reader:
        count += 1
        for column in columns:
            if len(row[column]) > 0 and cond(row):
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



@dataclass
class DataSource:
    filename: str
    fullname: bool
    name_columns: list[tuple[str,str]] | None = None
    fullname_columns: list[str] | None = None

def nocond(row: dict[str,str]) -> bool:
    return True

@dataclass
class DataQuery:
    name: str
    datasource: DataSource
    condition: Callable[[dict[str,str]], bool] = nocond

swimteam = DataSource(filename="input/swim_team.csv", fullname=False, name_columns=[ ["First Name", "Last Name"]])
waivers = DataSource(filename="output/member_waivers.csv", fullname=True, fullname_columns=["signer1", "signer2", "signer3", "signer4", "minor1", "minor2", "minor3", "minor4" ])

QUERY_LIST = [ DataQuery("swimteam", swimteam),
               DataQuery("waivers", waivers),
               DataQuery("complete_waivers", waivers, lambda x : x['complete'].lower() == 'y'),
               DataQuery("incomplete_waivers", waivers, lambda x : x['complete'].lower() == 'n') ]

QUERIES = { dq.name : dq for dq in QUERY_LIST }

def main(query: DataQuery):
    input_filename = query.datasource.filename
    fullnames = query.datasource.fullname

    input_file = open(input_filename, newline="")
    print(f"Note: reading names from '{input_filename}'")
    if fullnames:
        names = read_full_name_columns(input_file, query.datasource.fullname_columns, query.condition)
    else:
        member_names = read_name_columns(input_file, query.datasource.name_columns, query.condition)
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


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in QUERIES:
        print(f"Usage: {sys.argv[0]} <data query>")
        queries = [ i for i in QUERIES.keys() ]
        print(f"Sources: {', '.join(queries)}")
        sys.exit(-1)
    main(QUERIES[sys.argv[1]])
    
    

 
