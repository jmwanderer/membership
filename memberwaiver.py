"""
Member Waiver

Functionality to represent and manage member waiver records.
"""

from dataclasses import dataclass
import csv
import os


@dataclass
class Signature:
    # Adult signature on a member waiver
    name: str
    date: str


class MemberWaiver:
    """
    Represents data for a member waiver with CVS records
    """

    def __init__(self) -> None:
        # PDF file name in gdrive
        self.file_name: str = ""
        # Link to view the PDF
        self.web_view_link: str = ""
        self.signatures: list[Signature] = []
        # Minors listed
        self.minors: list[str] = []
        self.complete = "?"

    def __str__(self) -> str:
        result = self.file_name
        result += "\n\t" + self.web_view_link
        for signature in self.signatures:
            result += "\n\t" + str(signature.name) + " " + str(signature.date)
        for minor in self.minors:
            result += "\n\t" + str(minor)
        return result

    def is_complete(self) -> bool:
        return self.complete.lower() == "y"

    def set_complete(self, complete: bool) -> None:
        if complete:
            self.complete = "Y"
        else:
            self.complete = "N"

    # CSV fields
    FIELD_SIGNER1 = "signer1"
    FIELD_DATE1 = "date1"
    FIELD_SIGNER2 = "signer2"
    FIELD_DATE2 = "date2"
    FIELD_SIGNER3 = "signer3"
    FIELD_DATE3 = "date3"
    FIELD_SIGNER4 = "signer4"
    FIELD_DATE4 = "date4"
    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_COMPLETE = "complete"
    FIELD_LINK = "link"
    FIELD_FILENAME = "file"

    HEADER = [
        FIELD_DATE1,
        FIELD_SIGNER1,
        FIELD_DATE2,
        FIELD_SIGNER2,
        FIELD_DATE3,
        FIELD_SIGNER3,
        FIELD_DATE4,
        FIELD_SIGNER4,
        FIELD_MINOR1,
        FIELD_MINOR2,
        FIELD_MINOR3,
        FIELD_MINOR4,
        FIELD_COMPLETE,
        FIELD_LINK,
        FIELD_FILENAME,
    ]

    def get_row(self):
        """
        Generate a CSV row for the waiver
        """
        row = {}
        row[MemberWaiver.FIELD_LINK] = self.web_view_link
        row[MemberWaiver.FIELD_FILENAME] = self.file_name
        row[MemberWaiver.FIELD_COMPLETE] = self.complete

        for i, sig in enumerate(self.signatures):
            row[MemberWaiver.HEADER[i * 2]] = sig.date
            row[MemberWaiver.HEADER[i * 2 + 1]] = sig.name
        for i, name in enumerate(self.minors):
            row[MemberWaiver.HEADER[i + 8]] = name
        return row

    def read_row(self, row):
        """
        Initialize a waiver from a CSV row
        """
        self.web_view_link = row[MemberWaiver.FIELD_LINK]
        self.file_name = row[MemberWaiver.FIELD_FILENAME]
        if MemberWaiver.FIELD_COMPLETE in row:
            self.complete = row[MemberWaiver.FIELD_COMPLETE]

        self.signatures = []
        if len(row[MemberWaiver.FIELD_SIGNER1]) > 0:
            self.signatures.append(
                Signature(
                    name=row[MemberWaiver.FIELD_SIGNER1],
                    date=row[MemberWaiver.FIELD_DATE1],
                )
            )
        if len(row[MemberWaiver.FIELD_SIGNER2]) > 0:
            self.signatures.append(
                Signature(
                    name=row[MemberWaiver.FIELD_SIGNER2],
                    date=row[MemberWaiver.FIELD_DATE2],
                )
            )
        if len(row[MemberWaiver.FIELD_SIGNER3]) > 0:
            self.signatures.append(
                Signature(
                    name=row[MemberWaiver.FIELD_SIGNER3],
                    date=row[MemberWaiver.FIELD_DATE3],
                )
            )
        if len(row[MemberWaiver.FIELD_SIGNER4]) > 0:
            self.signatures.append(
                Signature(
                    name=row[MemberWaiver.FIELD_SIGNER4],
                    date=row[MemberWaiver.FIELD_DATE4],
                )
            )

        self.minors = []
        if len(row[MemberWaiver.FIELD_MINOR1]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR1])
        if len(row[MemberWaiver.FIELD_MINOR2]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR2])
        if len(row[MemberWaiver.FIELD_MINOR3]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR3])
        if len(row[MemberWaiver.FIELD_MINOR4]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR4])


memberwaiver_csv_filename = "output/member_waivers.csv"


def read_csv(csv_file: str = memberwaiver_csv_filename) -> list[MemberWaiver]:
    """
    Read waivers from a CSV file
    """
    result: list[MemberWaiver] = []

    if not os.path.exists(csv_file):
        print(f"Note: Starting with an empty waiver file: {csv_file}")
        return result

    print(f"Note: reading waiver file '{csv_file}'")

    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            waiver = MemberWaiver()
            waiver.read_row(row)
            result.append(waiver)
    print(f"Note: read {len(result)} waivers")
    return result


def write_csv(waivers: list[MemberWaiver], csv_file: str = memberwaiver_csv_filename):
    print(f"Note: writing waiver file '{csv_file}'")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MemberWaiver.HEADER)
        writer.writeheader()
        for waiver in waivers:
            writer.writerow(waiver.get_row())
        f.close()
    print(f"Note: wrote {len(waivers)} member waiver records.")


def simple_test() -> None:
    filename = "test_member_waivers.csv"

    # Expect an empty file
    waivers: list[MemberWaiver] = read_csv(filename)

    # Add records
    waiver = MemberWaiver()
    waiver.signatures.append(
        Signature("Bob", "2012-01-05")
    )
    waiver.minors.append("Sam")
    waiver.file_name = "waiver1.pdf"
    waiver.web_view_link = "http://web.com/waiver1.pdf"
    waivers.append(waiver)

    waiver = MemberWaiver()
    waiver.signatures.append(
        Signature("Erica", "2019-11-15")
    )
    waiver.signatures.append(
        Signature("Lionel", "2019-11-15")
    )
    waiver.minors.append("Parth")
    waiver.file_name = "waiver2.pdf"
    waiver.web_view_link = "http://web.com/waiver2.pdf"
    waivers.append(waiver)

    waiver = MemberWaiver()
    waiver.signatures.append(
        Signature("Adult1", "2019-11-01")
    )
    waiver.signatures.append(
        Signature("Adult2", "2019-11-02")
    )
    waiver.signatures.append(
        Signature("Adult3", "2019-11-03")
    )
    waiver.signatures.append(
        Signature("Adult4", "2019-11-04")
    )
    waiver.minors.append("Minor1")
    waiver.minors.append("Minor2")
    waiver.minors.append("Minor3")
    waiver.minors.append("Minor4")
    waiver.file_name = "waiver3.pdf"
    waiver.web_view_link = "http://web.com/waiver3.pdf"
    waivers.append(waiver)

    write_csv(waivers, filename)
    waivers = read_csv(filename)
    write_csv(waivers, filename)
    waivers = read_csv(filename)
    os.unlink(filename)


if __name__ == "__main__":
    simple_test()
