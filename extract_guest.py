"""
Extract guest waiver data from PDF files on Google drive.
"""

import os.path
import io
import pickle
import csv
import datetime


from googleapiclient.discovery import build

import parse_pdf
import guestwaiver
import dateutil
import gdrive


def main():
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    waivers: list[guestwaiver.GuestWaiver] = []

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
        file_data = gdrive.download_file(drive, file["id"])
        waiver_pdf = parse_pdf.parse_guest_waiver_pdf(file_data)
        print(waiver_pdf)
        file_name = file["name"]
        web_view_link = file["webViewLink"]
        print(web_view_link)
        waiver = guestwaiver.GuestWaiver()
        print(f"date {waiver_pdf.date}")
        _, date_signed = dateutil.find_date(waiver_pdf.date)
        waiver.date_signed = date_signed
        waiver.adult_signer = waiver_pdf.adult
        waiver.minors = waiver_pdf.minors.copy()
        waiver.file_name = file_name
        waiver.web_view_link = web_view_link
        waivers.append(waiver)

    guestwaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
