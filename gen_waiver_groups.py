"""
Determine sets of members for bulk requests of waiver signatures.

This automates trying to determine which people are parents that need to sign
family waivers, and which minors are include on the waiver.

3 types of results
- families with minor children  - request family waiver
- adults with no minor children - request signature of single person on a waiver
- unclear on parents - figure out who are parents, update parents.csv until empty
"""


import memberdata
from  waiverrec import MemberWaiverGroups, AdultRecord, FamilyRecord
import keys
import waiver_calcs


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


def generate_groups(membership: memberdata.Membership) -> MemberWaiverGroups:
    """
    Generate groups of waiver requests
    """
    groups = MemberWaiverGroups()
    member_keys = keys.gen_member_key_map(membership)

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
            record = AdultRecord(member)
            if member.member_id in member_keys:
                record.key_address = member_keys[member.member_id].member_email
            groups.no_minor_children.append(record)

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
                family = FamilyRecord()
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

        family = FamilyRecord()
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


def main():
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    # Create new groups
    groups = generate_groups(membership)
    groups.write_csv_files()

    # Update group status based on waiver documents
    waiver_calcs.update_waiver_status(membership)


if __name__ == "__main__":
    main()
