"""
Download and parse attestation files. Update output/attestations.csv

Skips files previously parsed.
"""

import time
from googleapiclient.discovery import build  # type: ignore

import docs
import parse_pdf
import gdrive

def move_new_signed_docs(drive, folder_src_name, folder_dst_name) -> int:

    count = 0
    folder_src_id = gdrive.get_folder_id(drive, folder_src_name)
    folder_dst_id = gdrive.get_folder_id(drive, folder_dst_name)

    print(f"Checking for new documents in Google Drive at '{folder_src_name}'")
    files = gdrive.get_file_list(drive, folder_src_name)
    for file in files:
        name: str = file['name']
        if name.endswith('pdf') and "Attestation" in name:
            print(f"move file {name}")
            count += 1
            gdrive.move_file(drive, file['id'], folder_dst_id)
    return count

def upload_attestation_csv_file(drive, local_file_name, remote_folder_name, remote_file_name):

    remote_folder_id = gdrive.get_folder_id(drive, remote_folder_name)
    remote_file_id = gdrive.get_file_id(drive, remote_folder_id, remote_file_name)
    if remote_file_id is None:
        print(f"Upload new file {remote_file_name} to {remote_folder_id}")
        gdrive.upload_csv_file(drive, remote_folder_id, remote_file_name, local_file_name)
    else:
        print(f"Update file {remote_file_id} in {remote_folder_id}")
        gdrive.update_csv_file(drive, remote_file_id, local_file_name)


def main(upload: bool = False) -> None:
    """
    Scrape all attestation PDF files and create a CSV file
    """
    attestations: list[docs.Attestation] = []
    attestations = docs.Attestation.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Household Attestations and Household Waivers"
    folder_src_name = "Requested signatures"
    count = move_new_signed_docs(drive, folder_src_name, folder_name)
    print(f"Moved {count} files.")

    if count > 0:
        print("Sleep 5 seconds for gdrive to sync.")
        time.sleep(5)

    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: set[str] = set(attestation.file_name for attestation in attestations)

    print("Processing Files:")
    skipped_count = 0
    parsed_count = 0
 
    for file in files:
        # Check if file has already been processed
        if file["name"] in filenames:
            #print(f"Note: already parsed {file['name']} - skipping")
            skipped_count += 1
            continue

        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file["id"])
        attestation_pdf = parse_pdf.parse_attestation_pdf(file_data)
        attestation_pdf.file_name = file["name"]
        attestation_pdf.web_view_link = file["webViewLink"]
        attestation = attestation_pdf.parse_attestation()
        attestations.append(attestation)
        parsed_count += 1

    print(f"Parsed {parsed_count} new documents. Skipped {skipped_count} existing documents.")
    if parsed_count > 0:
        docs.Attestation.write_csv(attestations)
        print(f"Wrote output: {docs.attestations_csv_filename}")
        # TODO: Should probably be done somewhere else - may be modified later
        print(f"Update attestations.csv to Google Drive in '{remote_folder_name}")
        remote_folder_name = "2025"
        if upload:
            upload_attestation_csv_file(drive, docs.attestatons_csv_filename, remote_folder_name, "attestations.csv")
        else:
            print("Skipping upload of attestations.csv")
 

if __name__ == "__main__":
    main()
