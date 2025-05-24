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
import waiverrec
import waiver_calcs


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

    waiver_calcs.update_waiver_complete(membership, groups, waivers)
    waiver_calcs.review_member_waiver_docs(membership, waivers)
    docs.MemberWaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
