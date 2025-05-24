"""
Download and parse guest waiver PDF files on Google drive.
Update guest_waivers.csv

Skips documents previously parsed.
"""

from googleapiclient.discovery import build  # type: ignore

import parse_pdf
import docs
import gdrive


def main() -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    waivers: list[docs.GuestWaiver] = []

    # Load existing waivers
    waivers = docs.GuestWaiver.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Guest Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: dict[str, bool] = {waiver.file_name: True for waiver in waivers}

    print("Processing Files:")
    for file in files:

        # Check if file has been parsed already.
        if file["name"] in filenames:
            print(f"Note: already parsed {file['name']} - skipping")
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

    docs.GuestWaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
