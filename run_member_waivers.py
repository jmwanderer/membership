"""
Master control file for member waiver process
"""

import sys
from googleapiclient.discovery import build  # type: ignore

import gdrive
import docs
import memberdata
import keys
import extract_attest
import extract_members
import gen_waiver_groups
import waiverrec
import waiver_calcs

upload: bool = False

def upload_member_waiver_records():
    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    remote_folder_name = docs.YEAR
    if upload:
        extract_members.upload_member_csv_file(drive, waiverrec.MemberRecord.member_csv, remote_folder_name, "member_records.csv")
    else:
        print("skipping upload of member_records.csv")

def main(command: str):
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.MemberKeys()
    member_keys.load_keys(membership)

    # Get new waiver files
    if command == "extract" or command == "all":
        print("Extract information from new documents.")
        extract_members.main(upload)
        extract_attest.main(upload)

    # Create new groups
    if command == "generate" or command == "all":
        print("Generate required waivers list")
        waiver_groups = gen_waiver_groups.generate_groups(membership, member_keys)
    else:
        waiver_groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)

    # Read latest attestations and member waivers
    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()

    if command == "review" or command == "all":
        print("Updating waiver status")
        # Update status on waiver docs - complete, OK, etc
        waiver_calcs.review_and_update_waivers(membership, waiver_groups, member_waivers, attestations)
        docs.MemberWaiver.write_csv(member_waivers)
        docs.Attestation.write_csv(attestations)

    if command == "update" or command == "all":
        waiver_calcs.update_waiver_record_status(waiver_groups, member_waivers, attestations)
        waiverrec.MemberWaiverGroups.write_csv_files(waiver_groups)
        waiver_calcs.report_waiver_record_stats(membership, waiver_groups, member_waivers, attestations, member_keys.member_key_map)

    # Generate and save member records
    if command == "records"  or command == "all":
        waiver_calcs.generate_single_signer_family_request(waiver_groups.with_minor_children, member_keys)
        waiver_calcs.generate_single_signer_request(waiver_groups.no_minor_children, member_keys)
        waiver_calcs.generate_member_records(waiver_groups, member_keys)
        upload_member_waiver_records()


arguments = ["all", "extract", "generate", "review", "update", "records"]

if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1] in arguments:
        print(f"Usage: run_member_waivers with one of: {arguments}")
        sys.exit(-1)
    main(sys.argv[1])
