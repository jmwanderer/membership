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
WAIVER_CSV_HEADER = [ "Acct#", "Member#", "First Name", "Last Name", "Type", "Signed", "Doc Link" ]


@dataclass
class SignedWaiver:
    """Represents an member covered by a waiver"""

    member: memberdata.MemberEntry
    doc_link: str
    
    


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

        waivers.append(SignedWaiver(members[0], entry.web_view_link))

    output_file = open(waiver_out_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow(WAIVER_CSV_HEADER)
    
    for waiver in waivers:
        output_csv.writerow([ waiver.member.account_num,
                              waiver.member.member_id, waiver.member.name.first_name, 
                              waiver.member.name.last_name, waiver.member.member_type,
                              "YES", waiver.doc_link ])
    output_file.close()
    print(f"Note: created {waiver_out_filename}")

if __name__ == "__main__":
    main()
