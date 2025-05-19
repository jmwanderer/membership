"""
Set or clear a field for rows matching account numbers or member ids.
Read:
    - output/account_ids.csv
    or
    - output/member_ids.csv

and update a given column for any matching rows.
"""

import argparse
import csv
import io
import os
import re
import sys

import memberdata


def read_csv_columns(
    stream: io.TextIOBase, col1: int, col2: int
) -> list[tuple[str, str]]:
    print(f"Note: reading CSV from stdin...")
    result = []
    count = 0
    reader = csv.reader(stream)
    for row in reader:
        count += 1
        if count == 1:
            continue
        entry = (row[col1], row[col2])
        result.append(entry)
    print(f"Note: read {len(result)} rows")
    return result


def lookup_accounts(
    membership: memberdata.Membership, entries: list[tuple[str, str]]
) -> list[str]:
    result: list[str] = []
    for last_name, first_name in entries:
        name = memberdata.MemberName(first_name, last_name)
        members = membership.find_members_by_name(name)
        if len(members) != 1:
            print(f"Warning: found {len(members)} for {name}")
            continue
        if members[0].account_num not in result:
            result.append(members[0].account_num)
    print(f"Lookup {len(result)} accounts.")
    return result


def get_backup_filename(filename: str):
    """
    Search for a backup filename not in use
    """
    m = re.match(r"(.+)\.csv", filename)
    if m is None:
        return None
    prefix = m.group(1)
    value = 1
    # Avoid an infinite loop in a hypothetical pathalogical case.
    while value < 10000:
        backup_name = f"{prefix}.{value}.csv"
        if not os.path.exists(backup_name):
            return backup_name
        value += 1
    return None


def read_ids_file(ids_filename: str) -> list[str]:
    ids_file = open(ids_filename, "r", newline="")
    ids_csv = csv.reader(ids_file)
    ids_list = []
    count = 0
    for row in ids_csv:
        count += 1
        if count == 1:
            continue
        ids_list.append(row[0])
    ids_file.close()
    print(f"Read {len(ids_list)} ids from {ids_filename}")
    return ids_list


def run_markup(
    filename: str,
    backup_filename: str,
    mark_col: str,
    clear_col: str,
    id_col: str,
    id_file: str,
):
    matched_ids = {}
    ids_list = read_ids_file(id_file)
    rows: list[dict[str, str]] = []

    # Read input file
    print(f"Update {filename} save backup to {backup_filename}")
    input_file = open(filename, "r", newline="")
    print(f"Note: reading {filename}")
    input_csv = csv.DictReader(input_file)
    if input_csv.fieldnames is None:
        print(f"Error: no field headers in {filename}")
        return
    column_names = list(input_csv.fieldnames)

    for row in input_csv:
        rows.append(row)
    input_file.close()
    print(f"Note: read {len(rows)} records")

    # Mark column for matching rows
    if len(mark_col) > 0:
        # Ensure column exists
        if mark_col not in column_names:
            column_names.append(mark_col)
        for row in rows:
            id_value = row[id_col]
            if id_value in ids_list:
                row[mark_col] = "x"
                matched_ids[id_value] = 1

    # Clear column for matching rows
    if len(clear_col) > 0:
        if clear_col not in column_names:
            column_names.append(clear_col)
        for row in rows:
            id_value = row[id_col]
            if id_value in ids_list:
                row[clear_col] = ""
                matched_ids[id_value] = 1

    # Backup original file
    os.rename(filename, backup_filename)

    # Write data out
    output_file = open(filename, "w", newline="")
    print(f"Note: writing {filename}")
    output_csv = csv.DictWriter(output_file, fieldnames=column_names)
    output_csv.writeheader()
    for row in rows:
        output_csv.writerow(row)
    output_file.close()
    print(f"Note: wrote {len(rows)} records")

    missed_ids = []
    for id_val in ids_list:
        if id_val not in matched_ids:
            missed_ids.append(id_val)

    if len(missed_ids) == 0:
        print("All ids found and updated")
    else:
        print(f"Matched ids ({len(matched_ids)}):")
        print(f"\t{', '.join(matched_ids)}")
        print(f"Missed ids ({len(missed_ids)}):")
        print(f"\t{', '.join(missed_ids)}")


def create_members_file(filename: str, mark_col: str, clear_col: str, id_file: str):

    membership = memberdata.Membership()
    membership.read_csv_files()
    ids_list = read_ids_file(id_file)

    column_names = ["Account#", "Member#", "Member Type", "First Name", "Last Name"]
    if len(mark_col) > 0:
        column_names.append(mark_col)
    if len(clear_col) > 0:
        column_names.append(clear_col)

    output_file = open(filename, "w", newline="")
    print(f"Note: created {filename}")
    output_csv = csv.DictWriter(output_file, fieldnames=column_names)
    output_csv.writeheader()

    count = 0
    for member in membership.all_members():
        count += 1
        row = {}
        row["Account#"] = member.account_num
        row["Member#"] = member.member_id
        row["Member Type"] = member.member_type
        row["First Name"] = member.name.first_name
        row["Last Name"] = member.name.last_name

        if member.member_id in ids_list:
            if len(mark_col) > 0:
                row[mark_col] = "x"
        output_csv.writerow(row)

    output_file.close()
    print(f"Note: wrote {count} member records")


def create_accounts_file(filename: str, mark_col: str, clear_col: str, id_file: str):

    membership = memberdata.Membership()
    membership.read_csv_files()
    ids_list = read_ids_file(id_file)

    column_names = ["Account#", "Account Type", "First Name", "Last Name"]
    if len(mark_col) > 0:
        column_names.append(mark_col)
    if len(clear_col) > 0:
        column_names.append(clear_col)

    output_file = open(filename, "w", newline="")
    print(f"Note: created {filename}")
    output_csv = csv.DictWriter(output_file, fieldnames=column_names)
    output_csv.writeheader()

    count = 0
    for account in membership.accounts():
        count += 1
        row = {}
        row["Account#"] = account.account_num
        row["Account Type"] = account.account_type
        row["First Name"] = account.billing_name.first_name
        row["Last Name"] = account.billing_name.last_name

        if account.account_num in ids_list:
            if len(mark_col) > 0:
                row[mark_col] = "x"
        output_csv.writerow(row)

    output_file.close()
    print(f"Note: wrote {count} account records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="updaterows", description="Set and clear fields on matching rows"
    )
    parser.add_argument("-m", "--mark_field", type=str, default="")
    parser.add_argument("-c", "--clear_field", type=str, default="")
    parser.add_argument("-i", "--id_type", type=str, default="account")
    parser.add_argument("filename")
    args = parser.parse_args(sys.argv[1:])

    filename = args.filename
    backup_filename = get_backup_filename(filename)
    if args.id_type == "account":
        id_col = "Account#"
        id_file = "output/account_ids.csv"
    elif args.id_type == "member":
        id_col = "Member#"
        id_file = "output/member_ids.csv"
    else:
        print("Error: id_type must be 'member' or 'acount'")
        sys.exit(-1)

    if backup_filename is None:
        print(f"Input file {filename} must end in .csv")
        sys.exit(-1)

    if os.path.exists(filename):
        run_markup(
            filename,
            backup_filename,
            args.mark_field,
            args.clear_field,
            id_col,
            id_file,
        )
    elif args.id_type == "account":
        create_accounts_file(filename, args.mark_field, args.clear_field, id_file)
    else:
        create_members_file(filename, args.mark_field, args.clear_field, id_file)
