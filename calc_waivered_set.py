"""
Generate list of members that have signed waivers

Input:
- mimbership data
- attestations.csv
- waiver_summary.csv

Output:
- signed_waivers.csv

"""

from dataclasses import dataclass 
import csv

import attest
import memberdata

waiver_out_filename = "output/signed_waivers.csv"
@dataclass
class SignedWaiver:
    """Represents an member covered by a waiver"""

    member: memberdata.MemberEntry
    doc_link: str
    waiver_signed: bool
    
    FIELD_ACCOUNT_NUM = "Acct#"
    FIELD_MEMBER_ID = "Member#"
    FIELD_FIRST_NAME = "First Name"
    FIELD_LAST_NAME  = "Last Name"
    FIELD_MEMBER_TYPE = "Type"
    FIELD_WAIVER_SIGNED = "Signed"
    FIELD_DOC_LINK = "Doc Link"

    def get_header():
        return [ SignedWaiver.FIELD_ACCOUNT_NUM, SignedWaiver.FIELD_MEMBER_ID, SignedWaiver.FIELD_FIRST_NAME, SignedWaiver.FIELD_LAST_NAME , SignedWaiver.FIELD_MEMBER_TYPE, SignedWaiver.FIELD_WAIVER_SIGNED, SignedWaiver.FIELD_DOC_LINK ]

    def get_row(self) -> dict[str,str]:
        row = { SignedWaiver.FIELD_ACCOUNT_NUM: self.member.account_num,
                SignedWaiver.FIELD_MEMBER_ID: self.member.member_id, 
                SignedWaiver.FIELD_FIRST_NAME: self.member.name.first_name, 
                SignedWaiver.FIELD_LAST_NAME: self.member.name.last_name, 
                SignedWaiver.FIELD_MEMBER_TYPE: self.member.member_type,
                SignedWaiver.FIELD_WAIVER_SIGNED: "YES", 
                SignedWaiver.FIELD_DOC_LINK:self.doc_link }
        return row



def main():
    attestations = attest.read_attestations_csv()
    membership = memberdata.Membership()
    membership.read_csv_files()

    waivers: list[SignedWaiver] = []

    for entry in attestations:
        signing_name = entry.adults[0].name
        signing_email = entry.adults[0].email
        members = membership.get_members_by_fullname(signing_name)
        if len(members) != 1:
            # Find member with matching email
            members = list(filter(lambda x : x.email == signing_email, members))
            
        if len(members) != 1:
            print(f"Error: unable to determine signer {signing_name} in doc {entry.web_view_link}")
            continue

        waivers.append(SignedWaiver(members[0], entry.web_view_link, True))

    output_file = open(waiver_out_filename, "w", newline="")
    output_csv = csv.DictWriter(output_file, fieldnames=SignedWaiver.get_header())
    output_csv.writeheader()
    
    for waiver in waivers:
        output_csv.writerow(waiver.get_row())
    output_file.close()
    print(f"Note: created {waiver_out_filename}")

if __name__ == "__main__":
    main()
