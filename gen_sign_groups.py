"""
Generate lists of members for types of signatures:
- families with minor children
- adults with no minor children
- unclear on parents

Outputs:
- parent_list_to_sign.csv
- adult_list_to_sign.csv
- unknown_list_to_sign.csv
"""

import csv

import csvfile
import memberdata
from memberdata import MemberEntry, AccountEntry, Membership
import keys


class FamilyRecord:
    def __init__(self, account_num: str):
        self.account_num = account_num
        self.adults: list[MemberEntry] = []
        self.minors: list[MemberEntry] = []


class MemberWaiverGroupings:

    def __init__(self) -> None:
        # Adult members with no minor children as members
        self.no_minor_children: list[MemberEntry] = []

        # Parents and minor children
        self.with_minor_children: list[FamilyRecord] = []

        # Adults potentially with minor children and minor children
        self.unknown_status: list[FamilyRecord] = []

        # Statistics for membership
        self.no_minors_count = 0
        self.unknown_parents_count = 0
        self.known_parents_count = 0


def select_possible_parents(
    membership: memberdata.Membership, account: memberdata.AccountEntry
) -> list[memberdata.MemberEntry]:
    """
    Identify adults that may be parents of minor children.
    """
    if not membership.has_minor_children(account.account_num):
        return []

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

    return possible_parents


def select_parents(
    membership: memberdata.Membership, account: memberdata.AccountEntry
) -> list[memberdata.MemberEntry]:
    """
    Guess which members are the parents of minor children.
    """
    possible_parents = select_possible_parents(membership, account)

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


def generate_groups(membership: Membership) -> MemberWaiverGroupings:
    groups = MemberWaiverGroupings()

    # Iterate through accounts
    for account in membership.active_member_accounts():
        # Only include active member accounts
        if not account.is_proprietary_member() and not account.is_alumni_pass():
            continue

        possible_parents = select_possible_parents(membership, account)
        members = membership.get_members_for_account_num(account.account_num)

        # Collect adults without minor aged children
        for member in members:
            if member.is_minor() or member in possible_parents:
                continue
            groups.no_minor_children.append(member)

        # If this account has no minor aged children, we are done with it
        if not membership.has_minor_children(account.account_num):
            groups.no_minors_count += 1
            continue

        # Check defined parent listings
        parent_recs = membership.get_families_for_account(account.account_num)
        if len(parent_recs) > 0:
            # Use defined rec instead of guessing
            num_minors = 0
            for parent_rec in parent_recs:
                family = FamilyRecord(account.account_num)
                for parent in parent_rec.parents:
                    family.adults.append(parent)
                for minor in parent_rec.minors:
                    num_minors += 1
                    family.minors.append(minor)
                groups.with_minor_children.append(family)
            if num_minors != membership.number_minor_children(account.account_num):
                print(f"Error: missing minor entries in account {account.account_num}")
            continue

        # Build list of parents and minor children
        # Collect adults with minor aged children
        parents = select_parents(membership, account)
        if len(parents) == 0:
            known_parents = False
            parents = possible_parents
            groups.unknown_parents_count += 1
        else:
            known_parents = True
            groups.known_parents_count += 1

        family = FamilyRecord(account.account_num)
        for member in parents:
            family.adults.append(member)
        for member in members:
            if member.is_minor():
                family.minors.append(member)

        if known_parents:
            groups.with_minor_children.append(family)
        else:
            groups.unknown_status.append(family)
    return groups


def write_groups(groups: MemberWaiverGroupings,
                 member_keys: dict[str,keys.KeyEntry]):

    # Create a list of adults that do not have minor children
    output_filename = "output/adults_no_minor_children.csv"
    csvfile.backup_file(output_filename)
    output_file = open(output_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    row = [csvfile.ACCOUNT_NUM, csvfile.MEMBER_ID, "name", "email_address","key_email"]
    output_csv.writerow(row)
    for member in groups.no_minor_children:
        key_email = ""
        if member.member_id in member_keys:
            key_email = member_keys[member.member_id].member_email
        row = [
            member.account_num,
            member.member_id,
            member.name.fullname(),
            member.email,
            key_email
        ]
        output_csv.writerow(row)
    output_file.close()
    print(f"Note: created file {output_filename}")

    # Create a list of parents and minor children
    output_filename = "output/parents_to_sign.csv"
    csvfile.backup_file(output_filename)
    output_file = open(output_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    row = [
        csvfile.ACCOUNT_NUM,
        "name",
        "email_address",
        "name2",
        "email_address2",
        "minor1",
        "minor2",
        "minor3",
        "minor4",
        "minor5",
    ]
    output_csv.writerow(row)
    for family in groups.with_minor_children:
        row = [family.account_num]
        for member in family.adults:
            row.extend([member.name.fullname(), member.email])
        while len(row) < 4:
            row.extend(["", ""])
        for member in family.minors:
            row.append(member.name.fullname())
        while len(row) < 10:
            row.extend([""])
        output_csv.writerow(row)
    output_file.close()
    print(f"Note: created file {output_filename}")

    # Create a list of families with unnkown parentage
    output_filename = "output/unknown_list_to_sign.csv"
    csvfile.backup_file(output_filename)
    output_file = open(output_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    row = [
        csvfile.ACCOUNT_NUM,
        "name",
        "email_address",
        "name2",
        "email_address2",
        "name3",
        "email_address3",
        "name4",
        "email_address4",
        "minor1",
        "minor2",
        "minor3",
        "minor4",
        "minor5",
    ]
    output_csv.writerow(row)
    for family in groups.unknown_status:
        row = [family.account_num]
        for member in family.adults:
            row.extend([member.name.fullname(), member.email])
        while len(row) < 8:
            row.extend(["", ""])
        for member in family.minors:
            row.append(member.name.fullname())
        while len(row) < 14:
            row.extend([""])
        output_csv.writerow(row)
    output_file.close()
    print(f"Note: created file {output_filename}")


def main():
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.gen_member_key_map(membership)

    groupings = generate_groups(membership)
    write_groups(groupings, member_keys)


if __name__ == "__main__":
    main()
