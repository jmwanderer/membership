"""
Download and parse member waiver PDF files on Google drive.
Update member_waivers.csv with information

Skips previously downloaded files
"""

from googleapiclient.discovery import build  # type: ignore

import memberdata
import parse_pdf
import memberwaiver
import gdrive


def check_waiver(
    membership: memberdata.Membership, waiver: memberwaiver.MemberWaiver
) -> bool:
    """
    Return True if waiver is considered to be complete.
    All required signatures and minors are included for a family waiver.
    A complete family waiver means that all minors and all signers are covered
    TODO: check that both parents have signed
    """

    if len(waiver.signatures) < 1:
        return False

    if waiver.type == memberwaiver.MemberWaiver.TYPE_INDIVIDUAL:
        return True

    name = waiver.signatures[0].name
    account = membership.get_account_by_fullname(name)
    if account is None:
        print(f"Warning: no account for name '{name}'")
        return False

    # Count number of minor children
    minors = 0
    for member in membership.get_members_for_account_num(account.account_num):
        if member.is_minor():
            minors += 1

    return minors == 0 or minors <= len(waiver.minors)


def main() -> None:
    """
    Scrape guest waiver PDF files and create a CSV file
    """
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    # Load existing waivers
    waivers: list[memberwaiver.MemberWaiver] = []
    waivers = memberwaiver.read_csv()

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
        waiver = memberwaiver.MemberWaiver()
        for signature in waiver_pdf.signatures:
            waiver.signatures.append(
                memberwaiver.Signature(signature.name, signature.date)
            )
        # Set type of waiver. We assume 1 sig, no minors is an individual waiver
        if len(waiver_pdf.signatures) > 1 or len(waiver_pdf.minors) > 0:
            waiver.type = memberwaiver.MemberWaiver.TYPE_FAMILY
        else:
            waiver.type = memberwaiver.MemberWaiver.TYPE_INDIVIDUAL

        waiver.minors = waiver_pdf.minors.copy()
        waiver.file_name = file_name
        waiver.web_view_link = web_view_link
        waiver.set_complete(check_waiver(membership, waiver))
        waivers.append(waiver)

    memberwaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
