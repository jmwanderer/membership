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
import csvfile



def read_ids_file(ids_filename: str) -> list[str]:
    """
    List a list of IDs from a CSV - assumed 1st column
    """
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
    """
    Read a CSV, make a backup, modify rows, and write the CSV

    Modifies rows that have an ID matching one of the ids read in.
    Row modifications are setting or clearning a column value. Adds the column if it doesn't exist.
    """
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

    if id_col not in input_csv.fieldnames:
        print(f"Error: looking to match {id_col} in {filename}, but it isn't there.")
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

    # TODO: consider using csvfile function
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


def create_members_file(filename: str):
    """
    Dump a file of the members for later markup.
    Used when the target file does not exist.
    """

    membership = memberdata.Membership()
    membership.read_csv_files()

    column_names = [
        csvfile.ACCOUNT_NUM,
        csvfile.MEMBER_ID,
        "Member Type",
        "First Name",
        "Last Name",
    ]

    output_file = open(filename, "w", newline="")
    print(f"Note: created {filename}")
    output_csv = csv.DictWriter(output_file, fieldnames=column_names)
    output_csv.writeheader()

    count = 0
    for member in membership.all_members():
        count += 1
        row = {}
        row[csvfile.ACCOUNT_NUM] = member.account_num
        row[csvfile.MEMBER_ID] = member.member_id
        row["Member Type"] = member.member_type
        row["First Name"] = member.name.first_name
        row["Last Name"] = member.name.last_name
        output_csv.writerow(row)

    output_file.close()
    print(f"Note: wrote {count} member records")


def create_accounts_file(filename: str):
    """
    Dump a file of the accounts for later markup.
    Used when the target file does not exist
    """

    membership = memberdata.Membership()
    membership.read_csv_files()

    column_names = [csvfile.ACCOUNT_NUM, "Account Type", "First Name", "Last Name"]
    output_file = open(filename, "w", newline="")
    print(f"Note: created {filename}")
    output_csv = csv.DictWriter(output_file, fieldnames=column_names)
    output_csv.writeheader()

    count = 0
    for account in membership.active_member_accounts():
        count += 1
        row = {}
        row[csvfile.ACCOUNT_NUM] = account.account_num
        row["Account Type"] = account.account_type
        row["First Name"] = account.billing_name.first_name
        row["Last Name"] = account.billing_name.last_name
        output_csv.writerow(row)

    output_file.close()
    print(f"Note: wrote {count} account records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="updaterows", description="Set and clear fields on matching rows"
    )

    parser.add_argument("idtype", choices=["account", "member"])
    parser.add_argument("-m", "--mark_field", type=str, default="")
    parser.add_argument("-c", "--clear_field", type=str, default="")
    parser.add_argument("filename")
    args = parser.parse_args(sys.argv[1:])

    filename = args.filename
    backup_filename = csvfile.get_backup_filename(filename)
    if args.idtype == "account":
        id_col = csvfile.ACCOUNT_NUM
        id_file = "output/account_ids.csv"
    elif args.idtype == "member":
        id_col = csvfile.MEMBER_ID
        id_file = "output/member_ids.csv"
    else:
        sys.exit(-1)

    if backup_filename is None:
        print(f"Input file {filename} must end in .csv")
        sys.exit(-1)

    if not os.path.exists(filename):
        # Create the file if necessary
        if args.idtype == "account":
            create_accounts_file(filename)
        else:
            create_members_file(filename)

    run_markup(
        filename,
        backup_filename,
        args.mark_field,
        args.clear_field,
        id_col,
        id_file,
    )
