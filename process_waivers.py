"""
Master control file for member waiver process
"""

import sys
from googleapiclient.discovery import build  # type: ignore

import gdrive
import docs
import memberdata
import keys
import gen_required_waivers
import waiverrec
import waiver_calcs

upload: bool = True

def upload_csv_file(drive, local_file_name, remote_folder_name, remote_file_name):

    remote_folder_id = gdrive.get_folder_id(drive, remote_folder_name)
    remote_file_id = gdrive.get_file_id(drive, remote_folder_id, remote_file_name)
    if remote_file_id is None:
        print(f"Upload new file {remote_file_name} to {remote_folder_id}")
        gdrive.upload_csv_file(drive, remote_folder_id, remote_file_name, local_file_name)
    else:
        print(f"Update file {remote_file_name} in {remote_folder_id}")
        gdrive.update_csv_file(drive, remote_file_id, local_file_name)


def upload_waiver_records():
    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    remote_folder_name = docs.YEAR
    if upload:
        upload_csv_file(drive, waiverrec.MemberRecord.member_csv, remote_folder_name, "member_records.csv")
    else:
        print("skipping upload of member_records.csv")
    remote_folder_name = "HelloSign"
    if upload:
        upload_csv_file(drive, memberdata.PARENTS_CSV, remote_folder_name, memberdata.PARENTS_CSV)
    else:
        print(f"skipping upload of {memberdata.PARENTS_CSV}")
 

def main():
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.MemberKeys()
    member_keys.load_keys(membership)

    # Create new groups
    print("Generate required waivers list")
    required_waivers = gen_required_waivers.generate(membership, member_keys)

    # Read latest attestations and member waivers
    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()

    print("Updating waiver status")
    # Update status on waiver docs - complete, OK, etc
    waiver_calcs.review_and_update_waivers(membership, required_waivers, member_waivers, attestations)
    docs.MemberWaiver.write_csv(member_waivers)
    docs.Attestation.write_csv(attestations)

    waiver_calcs.update_waiver_record_status(required_waivers, member_waivers, attestations)
    waiverrec.RequiredWaivers.write_csv_files(required_waivers)
    waiver_calcs.report_waiver_record_stats(membership, required_waivers, member_waivers, attestations, member_keys.member_key_map)

    # Generate and save member records
    waiver_calcs.generate_single_signer_family_request(required_waivers.with_minor_children, member_keys)
    waiver_calcs.generate_single_signer_request(required_waivers.no_minor_children, member_keys)
    waiver_calcs.generate_member_records(required_waivers, member_keys)
    upload_waiver_records()



if __name__ == "__main__":
    if "noupload" in sys.argv:
        upload = False
        print("Skip file uploading")
    main()
