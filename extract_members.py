"""
Download and parse member waiver PDF files on Google drive.
Update waiver docs: member_waivers.csv with information
Call waiver_calcs update and review functions to update member waiver records

Skips previously downloaded files
"""

import time
from googleapiclient.discovery import build  # type: ignore

import memberdata
import parse_pdf
import docs
import gdrive
import waiverrec
import waiver_calcs


def move_new_signed_docs(drive, folder_src_name, folder_dst_name):

    folder_src_id = gdrive.get_folder_id(drive, folder_src_name)
    folder_dst_id = gdrive.get_folder_id(drive, folder_dst_name)

    files = gdrive.get_file_list(drive, folder_src_name)
    for file in files:
        name: str = file['name']
        if name.endswith('pdf') and "Member" in name:
            print(f"move file {name}")
            gdrive.move_file(drive, file['id'], folder_dst_id)


def upload_member_csv_file(drive, local_file_name, remote_folder_name, remote_file_name):

    remote_folder_id = gdrive.get_folder_id(drive, remote_folder_name)
    remote_file_id = gdrive.get_file_id(drive, remote_folder_id, remote_file_name)
    if remote_file_id is None:
        print(f"Upload new file {remote_file_name} to {remote_folder_id}")
        with open(local_file_name, "r") as f:
            gdrive.upload_csv_file(drive, remote_folder_id, remote_file_name, f)
    else:
        print(f"Update file {remote_file_id} in {remote_folder_id}")
        with open(local_file_name, "r") as f:
            gdrive.update_csv_file(drive, remote_file_id, f)




def main() -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()
    groups = waiverrec.MemberWaiverGroups.read_csv_files(membership)

    # Load existing waivers
    waivers: list[docs.MemberWaiver] = []
    waivers = docs.MemberWaiver.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Member Waivers"

    folder_src_name = "Requested signatures"
    move_new_signed_docs(drive, folder_src_name, folder_name)

    print("Sleep 5 seconds for gdrive to sync.")
    time.sleep(5)

    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: dict[str, bool] = {waiver.file_name: True for waiver in waivers}

    print("Processing Files:")
    skipped_count = 0
    parsed_count = 0
    for file in files:
        # Check if file has already been parsed
        if file["name"] in filenames:
            #print(f"Note: already parsed {file['name']} - skipping")
            skipped_count += 1
            continue

        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file["id"])
        waiver_pdf = parse_pdf.parse_member_waiver_pdf(file_data)
        print(waiver_pdf)
        file_name = file["name"]
        web_view_link = file["webViewLink"]
        print(web_view_link)
        waiver = docs.MemberWaiver()
        for signature in waiver_pdf.signatures:
            waiver.signatures.append(
                docs.Signature(signature.name, signature.date)
            )
        # Set type of waiver. We assume 1 sig, no minors is an individual waiver
        if len(waiver_pdf.signatures) > 1 or len(waiver_pdf.minors) > 0:
            waiver.type = docs.MemberWaiver.TYPE_FAMILY
        else:
            waiver.type = docs.MemberWaiver.TYPE_INDIVIDUAL

        waiver.minors = waiver_pdf.minors.copy()
        waiver.file_name = file_name
        waiver.web_view_link = web_view_link
        waivers.append(waiver)
        parsed_count += 1

    print(f"Parsed {parsed_count} new documents. Skipped {skipped_count} existing documents.")
    docs.MemberWaiver.write_csv(waivers)

    # Update status of any waiver records
    waiver_calcs.update_waiver_status(membership)

    remote_folder_name = "2025 Member Waivers"
    upload_member_csv_file(drive, docs.memberwaiver_csv_filename, remote_folder_name, "member_waivers.csv")
    remote_folder_name = "2025"
    upload_member_csv_file(drive, waiverrec.MemberRecord.member_csv, remote_folder_name, "member_records.csv")

if __name__ == "__main__":
    main()
