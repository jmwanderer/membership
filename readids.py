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


def read_id_column(
    membership: memberdata.Membership, stream: io.TextIOBase
) -> list[memberdata.MemberEntry]:
    result = []
    count = 0
    reader = csv.DictReader(stream)
    for row in reader:
        member_id = row["Member#"]
        member = membership.get_member_by_id(member_id)
        if member is None:
            print(f"Warning: no member for id {member_id} found.")
            continue
        count += 1
        result.append(member)
    print(f"Note: found {len(result)} members")
    return result


def main(input_filename: str):
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    input_file = open(input_filename, newline="")
    members = read_id_column(membership, input_file)
    account_ids = []
    member_ids = []
    for member in members:
        if member.account_num not in account_ids:
            account_ids.append(member.account_num)
        if member.member_id not in member_ids:
            member_ids.append(member.member_id)
    input_file.close()

    # Write account ids
    accounts_filename = "output/account_ids.csv"
    output_file = open(accounts_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow(["Account#"])
    for entry in account_ids:
        output_csv.writerow([entry])
    output_file.close()
    print(f"Note: wrote {accounts_filename}")

    # Write member ids
    members_filename = "output/member_ids.csv"
    output_file = open(members_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow(["Member ID"])
    for entry in member_ids:
        output_csv.writerow([entry])
    output_file.close()
    print(f"Note: wrote {members_filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input file>")
        sys.exit(-1)
    main(sys.argv[1])
