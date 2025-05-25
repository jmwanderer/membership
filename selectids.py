"""
Run pre-programmed queries and load results as account and member ids.
The loaded ids are used by updaterows.py to alter the rows matching the loaded ids.

Queries:
- members / accounts that have signed an attestation
- members / accounts that have keys
- members / accounts with children on the swim team
- match ids and fullnames from specific files
- match firstname lastname from specific files

The IDs are stored in:
    - output/member_ids.csv
    - output/account_ids.csv
"""

from dataclasses import dataclass, field
from typing import Callable
import csv
import io
import sys

import memberdata
import csvfile


def read_name_columns(
    stream: io.TextIOBase,
    name_columns: list[tuple[str, str]],
    cond: Callable[[dict[str, str]], bool],
) -> list[memberdata.MemberName]:
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


def read_full_name_columns(
    stream: io.TextIOBase,
    columns: list[str],
    cond: Callable[[dict[str, str]], bool],
) -> list[str]:
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


def lookup_ids_member_names(
    membership: memberdata.Membership, member_names: list[memberdata.MemberName]
) -> tuple[set[str], set[str]]:
    """
    Translate a list of names (first, last) to a set of account and member ids
    """
    account_ids: set[str] = set()
    member_ids: set[str] = set()

    for name in member_names:
        members = membership.find_members_by_name(name)
        if len(members) == 0:
            print(f"Warning: could not find a member record matching {name}")
        elif len(members) > 1:
            print(f"Warning: found {len(members)} records matching {name}")

        for member in members:
            if member.account_num not in account_ids:
                account_ids.add(member.account_num)
            if member.member_id not in member_ids:
                member_ids.add(member.member_id)

    print(
        f"Lookup {len(account_ids)} unique accounts and {len(member_ids)} members from {len(member_names)} records."
    )
    return account_ids, member_ids


def lookup_ids_fullnames(
    membership: memberdata.Membership, fullnames: list[str]
) -> tuple[set[str], set[str]]:
    """
    Translate a list of names (full) to a set of account and member ids
    """
    account_ids: set[str] = set()
    member_ids: set[str] = set()

    for name in fullnames:
        members: list[memberdata.MemberEntry] = membership.get_members_by_fullname(name)

        if len(members) == 0:
            print(f"Warning: could not find a member record matching {name}")
        elif len(members) > 1:
            print(f"Warning: found {len(members)} records matching {name}")

        for member in members:
            account_ids.add(member.account_num)
            member_ids.add(member.member_id)

    print(
        f"Lookup {len(account_ids)} unique accounts and {len(member_ids)} members from {len(fullnames)} names."
    )
    return account_ids, member_ids


def write_ids(account_ids: set[str], member_ids: set[str]):
    """
    Save the sets of account and member ids to a CSV file for use by updaterows.py
    """
    accounts_filename = "output/account_ids.csv"
    output_file = open(accounts_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow([csvfile.ACCOUNT_NUM])
    for entry in account_ids:
        output_csv.writerow([entry])
    output_file.close()
    print(f"Note: wrote {len(account_ids)} records to {accounts_filename}")

    # Write member ids
    members_filename = "output/member_ids.csv"
    output_file = open(members_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow([csvfile.MEMBER_ID])
    for entry in member_ids:
        output_csv.writerow([entry])
    output_file.close()
    print(f"Note: wrote {len(member_ids)} records to {members_filename}")


@dataclass
class DataSource:
    """
    A file to query to match names in specific fields
    """

    filename: str
    fullname: bool
    name_columns: list[tuple[str, str]] = field(default_factory=list)
    fullname_columns: list[str] = field(default_factory=list)


def nocond(row: dict[str, str]) -> bool:
    return True


NOSRC = DataSource("", fullname=False)


@dataclass
class DataQuery:
    """
    A query that matches rows from a datasource that meet an optional condition test.
    """

    name: str
    datasource: DataSource
    condition: Callable[[dict[str, str]], bool] = nocond


# Match first and last name from the swim team file
swimteam = DataSource(
    filename="input/swim_team.csv",
    fullname=False,
    name_columns=[("First Name", "Last Name")],
)

# Match fullnames from multiple columns in the waiver record file.
family_waivers = DataSource(
    filename="output/member_waivers.csv",
    fullname=True,
    fullname_columns=[
        "signer1",
        "signer2",
        "signer3",
        "signer4",
        "minor1",
        "minor2",
        "minor3",
        "minor4",
    ],
)


# Source only adult signers on a waiver record
adult_waivers = DataSource(
    filename="output/member_waivers.csv",
    fullname=True,
    fullname_columns=[
        "signer1",
        "signer2",
        "signer3",
        "signer4",
    ],
)


# Source the signer on attestations
attest_signer = DataSource(
    filename="output/attestations.csv",
    fullname=True,
    fullname_columns=[
        "adult1",
    ],
)

# Match names in the keys file
keys = DataSource(
    filename="input/keys.csv",
    fullname=False,
    name_columns=[("FirstName", "LastName")],
)

# Match full names in a custom CSV file
fullnames = DataSource(
    filename="output/fullnames.csv", fullname=True, fullname_columns=["name"]
)
names = DataSource(
    filename="output/names.csv",
    fullname=False,
    name_columns=[("First Name", "Last Name")],
)

# Load IDs from a custom CSV file (member ids if present, otherwise account ids)
ids = DataSource(
    filename="output/ids.csv",
    fullname=False,
)


#
# Available queries
#
QUERY_LIST = [
    DataQuery("fullnames", fullnames),
    DataQuery("names", names),
    DataQuery("ids", ids),
    DataQuery("keys", keys),
    DataQuery("minors", NOSRC),
    DataQuery("swimteam", swimteam),
    DataQuery("attest_signer", attest_signer),
]

 
QUERIES = {dq.name: dq for dq in QUERY_LIST}


def load_data_query(
    membership: memberdata.Membership, query: DataQuery
) -> tuple[set[str], set[str]]:
    """
    Run a query and return the resulting account and member ID sets
    """
    input_filename = query.datasource.filename
    fullnames = query.datasource.fullname

    input_file = open(input_filename, newline="")
    print(f"Note: reading names from '{input_filename}'")
    if fullnames:
        print(f"Note: Reading fullname column(s) '{','.join(query.datasource.fullname_columns)}' from {input_filename}")
        names = read_full_name_columns(
            input_file, query.datasource.fullname_columns, query.condition
        )
    else:
        print(f"Note: Reading name columns '{','.join([str(x) for x in query.datasource.name_columns])}' from {input_filename}")
        member_names = read_name_columns(
            input_file, query.datasource.name_columns, query.condition
        )
    input_file.close()
    print("")

    print("Note: Looking up member names...")
    if fullnames:
        account_ids, member_ids = lookup_ids_fullnames(membership, names)
    else:
        account_ids, member_ids = lookup_ids_member_names(membership, member_names)
    return account_ids, member_ids


def load_ids_query(
    membership: memberdata.Membership, filename: str
) -> tuple[set[str], set[str]]:
    """
    Special function to load IDs as a query. Resolves the members and accounts during read.
    Called instead of load data query
    """
    input_file = open(filename, newline="")
    print(f"Note: reading ids from '{filename}'")
    reader = csv.DictReader(input_file)

    account_ids: set[str] = set()
    member_ids: set[str] = set()

    # Determine if we are reading member id or account number
    load_account_nums: bool = False
    load_member_ids: bool = False

    count = 0
    for row in reader:
        count += 1
        if not load_account_nums and not load_member_ids:
            # Favor member id first
            if csvfile.MEMBER_ID in row:
                print(f"Note: Reading '{csvfile.MEMBER_ID}' from '{filename}'")
                load_member_ids = True
            elif csvfile.ACCOUNT_NUM in row:
                print(f"Note: Reading '{csvfile.ACCOUNT_NUM}' from '{filename}'")
                load_account_nums = True

        if load_account_nums:
            account_id = row[csvfile.ACCOUNT_NUM]
            if account_id not in membership.account_nums():
                print(f"Warning: no account for id {account_id} found.")
                continue
            account_ids.add(row[csvfile.ACCOUNT_NUM])

        elif load_member_ids:
            member_id = row[csvfile.MEMBER_ID]
            member = membership.get_member_by_id(member_id)
            if member is None:
                print(f"Warning: no member for id {member_id} found.")
                continue
            member_ids.add(member_id)
            account_ids.add(member.account_num)

    entry_count = max(len(member_ids), len(account_ids))
    print(f"Note: read {entry_count} entries from {count} records")
    print("")
    return (account_ids, member_ids)

def load_minor_members(membership: memberdata.Membership) -> tuple[set[str], set[str]]:
    account_ids: set[str] = set()
    member_ids: set[str] = set()

    for member in membership.all_members():
        if member.is_minor():
            member_ids.add(member.member_id)
            account_ids.add(member.account_num)
    return (account_ids, member_ids)


def main(query: DataQuery):
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()
    print("")

    if query.name == "minors":
        account_ids, member_ids = load_minor_members(membership)
    elif query.name == "ids":
        account_ids, member_ids = load_ids_query(membership, query.datasource.filename)
    else:
        account_ids, member_ids = load_data_query(membership, query)
    write_ids(account_ids, member_ids)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in QUERIES:
        print(f"Usage: {sys.argv[0]} <data query>")
        queries = [i for i in QUERIES.keys()]
        print(f"Sources: {', '.join(queries)}")
        sys.exit(-1)
    main(QUERIES[sys.argv[1]])
