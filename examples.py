from __future__ import annotations
from dataclasses import dataclass
import csv


@dataclass
class Member:
    member_id: str
    name: str

    @staticmethod
    def readrow(row: dict[str, str]) -> Member:
        return Member(row["Member ID"], row["Last Name"].strip())


members_csv = csv.DictReader(open("input/members.csv"))
members = [Member.readrow(x) for x in members_csv]
print(f"Count: {len(members)} members")


keys_csv = csv.DictReader(open("input/keys.csv"))
members_csv = csv.DictReader(open("input/members.csv"))
members = {x["Last Name"].strip(): x for x in members_csv}
for key in keys_csv:
    if not key["LastName"] in members:
        print(f"Key assigned to non-member: {key['LastName']}")


@dataclass
class Key:
    name: str
    enabled: bool = True

    FIELD_NAME = "LastName"
    FIELD_ENABLED = "Access"

    @staticmethod
    def getheader() -> list[str]:
        return [Key.FIELD_NAME, Key.FIELD_ENABLED]

    def writerow(self) -> dict[str, str]:
        return {Key.FIELD_NAME: self.name, Key.FIELD_ENABLED: str(self.enabled)}


keys = [Key("Bob"), Key("John", False)]

with open("output/keys.csv", "w") as keys_file:
    keys_csv = csv.DictWriter(keys_file, fieldnames=Key.getheader())
    keys_csv.writeheader()
    keys_csv.writerows([x.writerow() for x in keys])
    keys_file.close()
