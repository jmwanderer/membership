"""
Download and parse guest waiver PDF files on Google drive.
Update guest_waivers.csv

Skips documents previously parsed.
"""

import time

from googleapiclient.discovery import build  # type: ignore

import parse_pdf
import docs
import gdrive


def move_new_signed_docs(drive, folder_src_name, folder_dst_name) -> int:

    folder_src_id = gdrive.get_folder_id(drive, folder_src_name)
    folder_dst_id = gdrive.get_folder_id(drive, folder_dst_name)

    files = gdrive.get_file_list(drive, folder_src_name)
    count = 0
    for file in files:
        name: str = file['name']
        if name.endswith('pdf') and "Guest" in name and docs.YEAR in name:
            print(f"move file {name}")
            count += 1
            gdrive.move_file(drive, file['id'], folder_dst_id)
    return count

def upload_guest_waiver_list(drive, local_file_name):
    remote_folder_name = docs.YEAR
    remote_file_name = "guest_waivers.csv"

    remote_folder_id = gdrive.get_folder_id(drive, remote_folder_name)
    remote_file_id = gdrive.get_file_id(drive, remote_folder_id, remote_file_name)
    print(f"Update file {remote_file_id} in {remote_folder_id}")
    gdrive.update_csv_file(drive, remote_file_id, local_file_name)


def run(upload: bool = False) -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    waivers: list[docs.GuestWaiver] = []

    # Load existing waivers
    waivers = docs.GuestWaiver.read_csv()

    folder_src_name = "Requested signatures"
    folder_name = f"{docs.YEAR} Guest Waivers"
    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    count = move_new_signed_docs(drive, folder_src_name, folder_name)

    if count > 0:
        print("Sleeping 5 seconds to ensure gdrive syncs")
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

        # Check if file has been parsed already.
        if file["name"] in filenames:
            #print(f"Note: already parsed {file['name']} - skipping")
            skipped_count += 1
            continue

        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file["id"])
        waiver_pdf = parse_pdf.parse_guest_waiver_pdf(file_data)
        print(waiver_pdf)
        file_name = file["name"]
        web_view_link = file["webViewLink"]
        print(web_view_link)
        waiver = docs.GuestWaiver()
        print(f"date {waiver_pdf.date}")
        waiver.date_signed = waiver_pdf.date
        waiver.adult_signer = waiver_pdf.adult
        waiver.minors = waiver_pdf.minors.copy()
        waiver.file_name = file_name
        waiver.web_view_link = web_view_link
        waivers.append(waiver)
        parsed_count += 1

    print(f"Parsed {parsed_count} new documents. Skipped {skipped_count} existing documents.")
    waivers.sort(key=docs.GuestWaiver.key_func)
    docs.GuestWaiver.write_csv(waivers)
    if upload:
        upload_guest_waiver_list(drive, docs.guestwaiver_csv_filename)
    else:
        print(f"Skipping upload of {docs.guestwaiver_csv_filename}")

