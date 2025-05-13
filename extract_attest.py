import os.path
import io
import pickle
import csv
import datetime

from googleapiclient.discovery import build

import attest
import gdrive


def main():
    """
    Scrape all attestation PDF files and create a CSV file
    
    TODO: update operation. Read CSV, scrape files, update, Write CSV
    TODO: handle multiple copies of one attestation?
    TODO: at least check for duplicates
    """
    attestations = []

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Household Attestations and Household Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    output_file = open(attest.attestations_csv_filename, "w", newline="")
    output_csv = csv.writer(output_file)
    output_csv.writerow(attest.Attestation.HEADER)

    print("Processing Files:")
    for file in files:
        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file['id'])
        attestation_pdf = attest.parse_attestation_pdf(file_data)
        attestation_pdf.file_name = file['name']
        attestation_pdf.web_view_link = file['webViewLink']
        attestation = attestation_pdf.parse_attestation()
        row = attestation.get_row()
        output_csv.writerow(row)

    output_file.close()
    print(f"Wrote output: {attest.attestations_csv_filename}")


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
