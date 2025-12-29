"""
Generate list of voting members
"""

import sys
from dataclasses import dataclass, field
import csv
import memberdata

@dataclass
class Vote:
    """Represents a membership vote"""
    account_num: str
    primary_member: memberdata.MemberName
    primary_email: str
    secondary_member: memberdata.MemberName | None = None
    secondary_email: str = ""
    valid: bool = False
    candidates: list[str] = field(default_factory=lambda: [])


def generate_vote_list(membership: memberdata.Membership ) -> list[Vote]:
    votes = []

    for account in membership.accounts():
        if not account.is_proprietary_member():
            continue
        vote = Vote(account.account_num, account.billing_name, account.email)
        votes.append(vote)
        print(f"added vote: {vote.primary_member}")

        primary_member = None
        other_members = []
        members = membership.get_members_for_account_num(account.account_num)
        for member in members:
            if not member.is_adult_type():
                continue
            if member.name == account.billing_name:
                primary_member = member
                continue
            other_members.append(member)
        
        if primary_member is None:
            print(f"Error finding primary {account.billing_name}")
            continue

        candidates = []
        for member in other_members:
            if not (primary_member.has_birthdate() and member.has_birthdate()):
                candidates.append(member)
                continue

            if abs(member.age() - primary_member.age()) < 20:
                candidates.append(member)

        if len(candidates) == 0:
            vote.valid = True
        elif len(candidates) == 1:
            vote.valid = True
            member = candidates[0]
            vote.secondary_member = member.name
            vote.secondary_email = member.email
        else:
            # TODO: pythonify
            for candidate in candidates:
                vote.candidates.append(str(candidate.name))

    return votes


HEADER_FIELDS = [ "ACCOUNT_NUM", "VALID", "PRIMARY_NAME", "PRIMARY_EMAIL",
                  "SECONDARY_NAME", "SECONDARY_EMAIL", "CANDIDATES" ]

def write_csv(votes: list[Vote], csv_file: str = "output/voters.csv") -> None:
    print(f"Writing {csv_file}")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames = HEADER_FIELDS)
        writer.writeheader()
        for vote in votes:
            row = { 
                "ACCOUNT_NUM": vote.account_num,
                "VALID": vote.valid,
                "PRIMARY_NAME": vote.primary_member,
                "PRIMARY_EMAIL": vote.primary_email,
                "SECONDARY_NAME": vote.secondary_member,
                "SECONDARY_EMAIL": vote.secondary_email,
                "CANDIDATES": ','.join(vote.candidates) }
            writer.writerow(row)


def main():
    membership = memberdata.Membership()
    membership.read_csv_files()
    votes = generate_vote_list(membership)
    write_csv(votes)
    

if __name__ == "__main__":
    print("Running gen_vote_rolls")
    main()
