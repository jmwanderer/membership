"""
Download and parse member waiver PDF files on Google drive.
Update member_waivers.csv with information

Skips previously downloaded files
"""

from googleapiclient.discovery import build  # type: ignore

import memberdata
import parse_pdf
import docs
import gdrive
import waiver_calcs


def main() -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    # Load existing waivers
    waivers: list[docs.MemberWaiver] = []
    waivers = docs.MemberWaiver.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Member Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: dict[str, bool] = {waiver.file_name: True for waiver in waivers}

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
        waiver.set_complete(waiver_calcs.check_waiver(membership, waiver))
        waivers.append(waiver)

    docs.MemberWaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
