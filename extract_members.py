"""
Extract guest waiver data from PDF files on Google drive.
"""

import os.path
import io
import pickle
import csv
import datetime


from googleapiclient.discovery import build     # type: ignore

import parse_pdf
import memberwaiver
import dateutil
import gdrive


def main() -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    waivers: list[memberwaiver.MemberWaiver] = []

    # Load existing waivers
    waivers = memberwaiver.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Member Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: dict[str,bool] = {waiver.file_name:True for waiver in waivers}

    print("Processing Files:")
    for file in files:
        # Check if file has already been parsed
        if file["name"] in filenames:
            print(f"Note: already parsed {file['name']} - skipping")
            continue

        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file["id"])
        waiver_pdf = parse_pdf.parse_member_waiver_pdf(file_data)
        print(waiver_pdf)
        file_name = file["name"]
        web_view_link = file["webViewLink"]
        print(web_view_link)
        waiver = memberwaiver.MemberWaiver()
        for signature in waiver_pdf.signatures:
            waiver.signatures.append(
                memberwaiver.Signature(signature.name, signature.date)
            )
        waiver.minors = waiver_pdf.minors.copy()
        waiver.file_name = file_name
        waiver.web_view_link = web_view_link
        waivers.append(waiver)

    memberwaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
