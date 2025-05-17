"""
Guest Waiver

Functionality to represent and manage guest waiver records.
"""

import csv
import os


class GuestWaiver:
    """
    Represents data for a guest waiver.
    Supports CVS records
    """

    def __init__(self) -> None:
        # PDF file name in gdrive
        self.file_name: str = ""
        # Link to view the PDF
        self.web_view_link: str = ""
        self.adult_signer: str = ""
        # Minors listed
        self.minors: list[str] = []
        self.date_signed: str = ""

    def __str__(self) -> str:
        result = self.file_name
        result += "\n\t" + self.web_view_link
        result += "\n\t" + str(self.adult_signer)
        for minor in self.minors:
            result += "\n\t" + str(minor)

        return result

    # CSV fields
    FIELD_DATE = "date"
    FIELD_SIGNER = "signer"
    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_LINK = "link"
    FIELD_FILENAME = "file"

    HEADER = [
        FIELD_DATE,
        FIELD_SIGNER,
        FIELD_MINOR1,
        FIELD_MINOR2,
        FIELD_MINOR3,
        FIELD_MINOR4,
        FIELD_LINK,
        FIELD_FILENAME,
    ]

    def get_row(self):
        """
        Generate a CSV row for the waiver
        """
        row = {}
        row[GuestWaiver.FIELD_LINK] = self.web_view_link
        row[GuestWaiver.FIELD_FILENAME] = self.file_name
        row[GuestWaiver.FIELD_DATE] = self.date_signed
        row[GuestWaiver.FIELD_SIGNER] = self.adult_signer
        for i, name in enumerate(self.minors):
            row[GuestWaiver.HEADER[i + 2]] = name
        return row

    def read_row(self, row):
        """
        Initialize a waiver from a CSV row
        """
        self.web_view_link = row[GuestWaiver.FIELD_LINK]
        self.file_name = row[GuestWaiver.FIELD_FILENAME]
        self.date_signed = row[GuestWaiver.FIELD_DATE]
        self.adult_signer = row[GuestWaiver.FIELD_SIGNER]

        self.minors = []
        if len(row[GuestWaiver.FIELD_MINOR1]) > 0:
            self.minors.append(row[GuestWaiver.FIELD_MINOR1])
        if len(row[GuestWaiver.FIELD_MINOR2]) > 0:
            self.minors.append(row[GuestWaiver.FIELD_MINOR2])
        if len(row[GuestWaiver.FIELD_MINOR3]) > 0:
            self.minors.append(row[GuestWaiver.FIELD_MINOR3])
        if len(row[GuestWaiver.FIELD_MINOR4]) > 0:
            self.minors.append(row[GuestWaiver.FIELD_MINOR4])


guestwaiver_csv_filename = "output/guest_waivers.csv"


def read_csv(csv_file: str = guestwaiver_csv_filename) -> list[GuestWaiver]:
    """
    Read waivers from a CSV file
    """
    result: list[GuestWaiver] = []

    if not os.path.exists(csv_file):
        print(f"Note: starting with an empty waiver file")
        return result

    print(f"Note: reading waiver file '{csv_file}'")

    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            waiver = GuestWaiver()
            waiver.read_row(row)
            result.append(waiver)
    print(f"Note: read {len(result)} waivers")
    return result


def write_csv(waivers: list[GuestWaiver], csv_file: str = guestwaiver_csv_filename):
    print(f"Note: writing waiver file '{csv_file}'")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GuestWaiver.HEADER)
        writer.writeheader()
        for waiver in waivers:
            writer.writerow(waiver.get_row())
        f.close()
    print(f"Note: wrote {len(waivers)} guest waiver records.")


def simple_test() -> None:
    waivers: list[GuestWaiver] = []

    waiver_filename: str = "test_guest_waivers.csv"
    # Empty file
    write_csv(waivers, waiver_filename)
    read_csv()

    # Add records
    waiver = GuestWaiver()
    waiver.adult_signer = "Bob"
    waiver.minors.append("Sam")
    waiver.date_signed = "2012-01-05"
    waiver.file_name = "waiver1.pdf"
    waiver.web_view_link = "http://web.com/waiver1.pdf"
    waivers.append(waiver)

    waiver = GuestWaiver()
    waiver.adult_signer = "Erica"
    waiver.minors.append("Parth")
    waiver.date_signed = "2018-10-21"
    waiver.file_name = "waiver2.pdf"
    waiver.web_view_link = "http://web.com/waiver2.pdf"
    waivers.append(waiver)
    write_csv(waivers, waiver_filename)
    waivers = read_csv()
    os.unlink(waiver_filename)


if __name__ == "__main__":
    simple_test()
