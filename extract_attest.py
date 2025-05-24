"""
Download and parse attestation files. Update output/attestations.csv

Skips files previously parsed.
"""

from googleapiclient.discovery import build  # type: ignore

import docs
import parse_pdf
import gdrive


def main() -> None:
    """
    Scrape all attestation PDF files and create a CSV file
    """
    attestations: list[docs.Attestation] = []
    attestations = docs.Attestation.read_csv()

    gdrive.login()
    drive = build("drive", "v3", credentials=gdrive.creds)
    folder_name = "2025 Household Attestations and Household Waivers"
    files = gdrive.get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
        return

    filenames: set[str] = set(attestation.file_name for attestation in attestations)

    print("Processing Files:")
    for file in files:
        # Check if file has already been processed
        if file["name"] in filenames:
            print(f"Note: already parsed {file['name']} - skipping")
            continue

        print(f"{file['name']}")
        file_data = gdrive.download_file(drive, file["id"])
        attestation_pdf = parse_pdf.parse_attestation_pdf(file_data)
        attestation_pdf.file_name = file["name"]
        attestation_pdf.web_view_link = file["webViewLink"]
        attestation = attestation_pdf.parse_attestation()
        attestations.append(attestation)

    docs.Attestation.write_csv(attestations)
    print(f"Wrote output: {docs.attestations_csv_filename}")


if __name__ == "__main__":
    main()
