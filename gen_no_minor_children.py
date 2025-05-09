"""
Generate list of adults that do not have minor aged children

Input: memberdata
Output: not_parent_list.csv
"""

import csv
import memberdata
from gen_parent_list import select_possible_parents

# Filenames
output_filename = "output/adults_no_minor_children.csv"

def main():
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    # Create a list of adults that do not have minor children
    output_file = open(output_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    row = [ "Account#", "Member#", "name", "email_address" ]
    output_csv.writerow(row)

    for account in membership.accounts():
        # Only include active member accounts
        if not account.is_proprietary_member() and not account.is_alumni_pass():
            continue
        members = membership.get_members_for_account_num(account.account_num)
        possible_parents = select_possible_parents(membership, account)
        for member in members:
            if member.is_child_type() or member in possible_parents:
                continue
            row = [ member.account_num, member.member_id, member.name.fullname(), member.email ]
            output_csv.writerow(row)
    output_file.close()
    print(f"Note: created file {output_filename}")


if __name__ == "__main__":
    main()




