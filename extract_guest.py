"""
Extract guest waiver data from PDF files on Google drive.
"""

import os.path
import io
import pickle
import csv
import datetime

from googleapiclient.discovery import build

import parse_guest
import gdrive


def main():
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    waivers: list[parse_guest.GuestWaiverPDF] = []

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Guest Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    print("Processing Files:")
    for file in files:
        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file['id'])
        waiver_pdf = parse_guest.parse_waiver_pdf(file_data)
        print(waiver_pdf)
        file_name = file['name']
        web_view_link = file['webViewLink']
        print(web_view_link)



def test_load_attestations():
    attestations = attest.read_attestations_csv()

    for attestation in attestations:
        print(f"file: {attestation.file_name}")
        print(f"weblink: {attestation.web_view_link}")
        for adult in attestation.adults:
            print(f"Adult: {adult.name}, email: {adult.email}, birthday: {adult.birthdate}")
        for child in attestation.minors:
            print(f"Child: {child.name}, email: {child.email}, birthday: {child.birthdate}")
        print()


if __name__ == "__main__":
    #test_load_attestations()
    main()
