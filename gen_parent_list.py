"""
Generate list of member parents with minor children.

Create two lists - one for single parent and one for double parent households

Input: members.csv, accounts.csv
Output: parents.csv
"""

import csv
import memberdata


def has_minor_children(membership: memberdata.Membership, account_num: str) -> bool:
    for member in membership.get_members_for_account_num(account_num):
        if member.is_minor():
            return True
    return False


def select_parents(
    membership: memberdata.Membership, account: memberdata.AccountEntry
) -> list[memberdata.MemberEntry]:
    """
    Guess which members are the parents of minor children.
    """
    members = membership.get_members_for_account_num(account.account_num)

    # get minor min age
    # get minor max age
    num_minors = 0
    min_minor = 18
    max_minor = 0
    for member in members:
        if member.is_minor():
            # Assumed minor child
            num_minors += 1
            if member.has_birthdate():
                min_minor = min(min_minor, member.age())
                max_minor = max(max_minor, member.age())

    # find adults in age range relative to minor children
    possible_parents = []
    for member in members:
        if not member.is_adult_type():
            continue

        if member.has_birthdate() and member.age() - max_minor < 19:
            continue

        if member.has_birthdate() and member.age() - min_minor > 55:
            continue

        possible_parents.append(member)

    # if > 15 years between parents, not sure
    if len(possible_parents) == 2:
        member1 = possible_parents[0]
        member2 = possible_parents[1]
        if (
            member1.has_birthdate()
            and member2.has_birthdate()
            and abs(member1.age() - member2.age()) > 16
        ):
            possible_parents = []

    if len(possible_parents) > 2:
        possible_parents = []

    return possible_parents


def dump_results(membership: memberdata.Membership):
    known_parents = 0
    unknown_parents = 0
    no_minors = 0

    # Iterate over all accounts
    for account_entry in membership.accounts():
        if not has_minor_children(membership, account_entry.account_num):
            no_minors += 1
            continue

        print(f"\nAccount {account_entry.account_num} : {account_entry.billing_name}")
        parents = select_parents(membership, account_entry)
        members = membership.get_members_for_account_num(account_entry.account_num)

        if len(parents) == 0:
            unknown_parents += 1
            print("Don't know who are the parents")
            print("Not Minor:")
            for member in members:
                if not member.is_minor():
                    print(f"\t{member.name} birthday: {member.birthdate}")

            print("Minors:")
            for member in members:
                if member.is_minor():
                    print(f"\t{member.name} birthday: {member.birthdate}")

        else:
            known_parents += 1
            print("Parents:")
            for parent in parents:
                print(f"\t{parent.name} birthday: {parent.birthdate}")
            print("Not parents:")
            for member in members:
                if not member.is_minor() and not member in parents:
                    print(f"\t{member.name} birthday: {member.birthdate}")

            print("Minors:")
            for member in members:
                if member.is_minor():
                    print(f"\t{member.name} birthday: {member.birthdate}")

    print(
        f"No minors {no_minors}, Known Parents {known_parents}, Unknown Parents {unknown_parents}"
    )


# Filenames
output_filename = "output/parent_list.csv"

# Read membership data
membership = memberdata.Membership()
membership.read_csv_files()


# Create a list of parents of minor children
output_file = open(output_filename, "w", newline="")
output_csv = csv.writer(output_file)
row = ["Account#", "name", "email_address", "name2", "email_address2", "minors"]
output_csv.writerow(row)

no_minors_count = 0
unknown_parents_count = 0
known_parents_count = 0

# Iterate through accounts and make entries for those with minor children
for account_entry in membership.accounts():
    if account_entry.is_staff():
        continue

    if not has_minor_children(membership, account_entry.account_num):
        no_minors_count += 1
        continue

    # print(f"Processing account {account_entry.account_num} : {account_entry.billing_name}")
    parents = select_parents(membership, account_entry)

    name = ""
    email = ""
    name2 = ""
    email2 = ""
    minors = ""

    if len(parents) == 0:
        unknown_parents_count += 1
    else:
        known_parents_count += 1
        name = str(parents[0].name)
        email = parents[0].email

    if len(parents) > 1:
        name2 = str(parents[1].name)
        email2 = parents[1].email

    members = membership.get_members_for_account_num(account_entry.account_num)
    minor_list = []
    for member in members:
        if member.is_minor():
            minor_list.append(str(member.name))
    minors = ";".join(minor_list)

    row = [account_entry.account_num, name, email, name2, email2, minors]
    output_csv.writerow(row)

output_file.close()

print(
    f"Generated {output_filename} with {unknown_parents_count + known_parents_count} entries."
)
print(f"\t{unknown_parents_count} entries need manual configuration")
print(f"\tAccounts with no minor children: {no_minors_count}")
