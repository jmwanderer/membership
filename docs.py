"""
Models for signed documents:
    - MemberWaiver
        - for individuals
        - families with minor children
    - GuestWaiver
    - Household Attestations
        - record a signer plus adults and minors in the household, pointer to the PDF.

All saved as a row in CSV files.
"""

from __future__ import annotations
from dataclasses import dataclass
import datetime
import csv
import os

import csvfile


@dataclass
class Signature:
    # Adult signature on a member waiver
    name: str
    date: str

    @staticmethod
    def last_name(fullname: str) -> str:
        index = fullname.rfind(' ')
        if index == -1:
            return fullname
        return fullname[index+1:]


memberwaiver_csv_filename = "data/member_waivers.csv"

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
        self.type = "?"
        self.reviewed = "?"

    def __str__(self) -> str:
        result = self.file_name
        result += "\n\t" + self.web_view_link
        for signature in self.signatures:
            result += "\n\t" + str(signature.name) + " " + str(signature.date)
        for minor in self.minors:
            result += "\n\t" + str(minor)
        return result

    def is_complete(self) -> bool:
        """
        True means all minors are covered in waiver
        """
        return csvfile.is_true_value(self.complete)

    def is_reviewed(self) -> bool:
        return self.reviewed.lower() == "y"

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
    FIELD_MINOR1 = "minor1"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR4 = "minor4"
    FIELD_MINOR5 = "minor5"
    FIELD_TYPE = "type"
    FIELD_COMPLETE = "minors_complete"
    FIELD_REVIEWED = "reviewed"
    FIELD_LINK = "link"
    FIELD_FILENAME = "file"

    TYPE_INDIVIDUAL = "individual"
    TYPE_FAMILY = "family"

    HEADER = [
        FIELD_REVIEWED,
        FIELD_DATE1,
        FIELD_SIGNER1,
        FIELD_DATE2,
        FIELD_SIGNER2,
        FIELD_MINOR1,
        FIELD_MINOR2,
        FIELD_MINOR3,
        FIELD_MINOR4,
        FIELD_MINOR5,
        FIELD_TYPE,
        FIELD_COMPLETE,
        FIELD_LINK,
        FIELD_FILENAME,
    ]

    def get_row(self):
        """
        Generate a CSV row for the waiver
        """
        row = {}
        if len(self.signatures) > 0:
            row[MemberWaiver.HEADER[1]] = self.signatures[0].date
            row[MemberWaiver.HEADER[2]] = self.signatures[0].name
        if len(self.signatures) > 1:
            row[MemberWaiver.HEADER[3]] = self.signatures[1].date
            row[MemberWaiver.HEADER[4]] = self.signatures[1].name

        for i, name in enumerate(self.minors):
            row[MemberWaiver.HEADER[i + 5]] = name

        # Write these second to avoid above loops from overwriting
        row[MemberWaiver.FIELD_LINK] = self.web_view_link
        row[MemberWaiver.FIELD_FILENAME] = self.file_name
        row[MemberWaiver.FIELD_TYPE] = self.type
        row[MemberWaiver.FIELD_COMPLETE] = self.complete
        row[MemberWaiver.FIELD_REVIEWED] = self.reviewed
        return row

    def read_row(self, row):
        """
        Initialize a waiver from a CSV row
        """
        self.web_view_link = row[MemberWaiver.FIELD_LINK]
        self.file_name = row[MemberWaiver.FIELD_FILENAME]
        self.reviewed = row[MemberWaiver.FIELD_REVIEWED]
        if MemberWaiver.FIELD_COMPLETE in row:
            self.complete = row[MemberWaiver.FIELD_COMPLETE]
        if MemberWaiver.FIELD_REVIEWED in row:
            self.type = row[MemberWaiver.FIELD_REVIEWED]
        if MemberWaiver.FIELD_TYPE in row:
            self.type = row[MemberWaiver.FIELD_TYPE]

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

        self.minors = []
        if len(row[MemberWaiver.FIELD_MINOR1]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR1])
        if len(row[MemberWaiver.FIELD_MINOR2]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR2])
        if len(row[MemberWaiver.FIELD_MINOR3]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR3])
        if len(row[MemberWaiver.FIELD_MINOR4]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR4])
        if len(row[MemberWaiver.FIELD_MINOR5]) > 0:
            self.minors.append(row[MemberWaiver.FIELD_MINOR5])



    @staticmethod
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

    @staticmethod
    def write_csv(waivers: list[MemberWaiver], csv_file: str = memberwaiver_csv_filename):

        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: writing waiver file '{csv_file}'")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=MemberWaiver.HEADER)
            writer.writeheader()
            for waiver in waivers:
                writer.writerow(waiver.get_row())
            f.close()
        print(f"Note: wrote {len(waivers)} member waiver records.")

    @staticmethod
    def create_doc_map(member_waivers: list[MemberWaiver]) -> dict[str,MemberWaiver]:
        """
        Create a dictionary of selected waivers for each person.
        We find the best waiver associated with a person.
        TODO: May need to build a list first and then select the best waiver from the list.
        TODO: consider 1 function taking attestations and waivers
        """
        doc_map: dict[str, MemberWaiver] = {}
        for waiver_doc in member_waivers:
            for signature in waiver_doc.signatures:
                # Use lower case name
                name = signature.name.lower()
                current_waiver_doc = doc_map.get(name)

                # If no waiver yet identified, take this one
                if current_waiver_doc is None:
                    doc_map[name] = waiver_doc
                    continue

                # Don't replace a family waiver with an individual
                if current_waiver_doc.type != MemberWaiver.TYPE_FAMILY:
                    doc_map[name] = waiver_doc
                    continue

                # Prefer the complete waiver
                if not current_waiver_doc.is_complete():
                    doc_map[name] = waiver_doc

        return doc_map


# Default location to store attestations.
attestations_csv_filename = "data/attestations.csv"


@dataclass
class AttestEntry:
    """Person entry for an attestation"""

    name: str
    email: str
    birthdate: datetime.date


class Attestation:
    """
    Attestaton represtened as a line in a CSV file
    """

    def __init__(self) -> None:
        self.file_name: str = ""
        self.web_view_link: str = ""
        self.complete = "?"
        self.reviewed: str = ""
        self.adults: list[AttestEntry] = []
        self.minors: list[AttestEntry] = []

    def __str__(self) -> str:
        result = self.file_name
        result += "\n\t" + self.web_view_link
        for adult in self.adults:
            result += "\n\t" + str(adult)
        for minor in self.minors:
            result += "\n\t" + str(minor)

        return result

    def is_reviewed(self) -> bool:
        return csvfile.is_true_value(self.reviewed)

    def is_complete(self) -> bool:
        """
        True means that all minors are covered in waiver.
        """
        return csvfile.is_true_value(self.complete)

    def set_complete(self, complete: bool) -> None:
        if complete:
            self.complete = "Y"
        else:
            self.complete = "N"

    # CSV fields
    FIELD_ADULT1 = "adult1"
    FIELD_ADULT1_EMAIL = "adult1_email"
    FIELD_ADULT1_BIRTHDATE = "adult1_birthdate"
    FIELD_ADULT2 = "adult2"
    FIELD_ADULT2_EMAIL = "adult2_email"
    FIELD_ADULT2_BIRTHDATE = "adult2_birthdate"
    FIELD_ADULT3 = "adult3"
    FIELD_ADULT3_EMAIL = "adult3_email"
    FIELD_ADULT3_BIRTHDATE = "adult3_birthdate"
    FIELD_ADULT4 = "adult4"
    FIELD_ADULT4_EMAIL = "adult4_email"
    FIELD_ADULT4_BIRTHDATE = "adult4_birthdate"
    FIELD_MINOR1 = "minor1"
    FIELD_MINOR1_BIRTHDATE = "minor1_birthdate"
    FIELD_MINOR2 = "minor2"
    FIELD_MINOR2_BIRTHDATE = "minor2_birthdate"
    FIELD_MINOR3 = "minor3"
    FIELD_MINOR3_BIRTHDATE = "minor3_birthdate"
    FIELD_MINOR4 = "minor4"
    FIELD_MINOR4_BIRTHDATE = "minor4_birthdate"
    FIELD_MINOR5 = "minor5"
    FIELD_MINOR5_BIRTHDATE = "minor5_birthdate"
    FIELD_REVIEWED = "reviewed"
    FIELD_COMPLETE = "minors_complete"
    FIELD_LINK = "link"
    FIELD_NAME = "name"

    HEADER = [
        FIELD_ADULT1,
        FIELD_ADULT1_EMAIL,
        FIELD_ADULT1_BIRTHDATE,
        FIELD_ADULT2,
        FIELD_ADULT2_EMAIL,
        FIELD_ADULT2_BIRTHDATE,
        FIELD_ADULT3,
        FIELD_ADULT3_EMAIL,
        FIELD_ADULT3_BIRTHDATE,
        FIELD_ADULT4,
        FIELD_ADULT4_EMAIL,
        FIELD_ADULT4_BIRTHDATE,
        FIELD_MINOR1,
        FIELD_MINOR1_BIRTHDATE,
        FIELD_MINOR2,
        FIELD_MINOR2_BIRTHDATE,
        FIELD_MINOR3,
        FIELD_MINOR3_BIRTHDATE,
        FIELD_MINOR4,
        FIELD_MINOR4_BIRTHDATE,
        FIELD_MINOR5,
        FIELD_MINOR5_BIRTHDATE,
        FIELD_COMPLETE,
        FIELD_REVIEWED,
        FIELD_LINK,
        FIELD_NAME,
    ]

    def get_row(self):
        """
        Generate a CSV row for this attestation
        """
        row = [""] * 26
        row[22] = self.complete
        row[23] = self.reviewed
        row[24] = self.file_name
        row[25] = self.web_view_link

        index = 0
        for adult in self.adults:
            row[index] = adult.name
            row[index + 1] = adult.email
            if adult.birthdate != datetime.date.min:
                row[index + 2] = adult.birthdate.isoformat()
            index += 3

        index = 12
        for minor in self.minors:
            row[index] = minor.name
            if minor.birthdate != datetime.date.min:
                row[index + 1] = minor.birthdate.isoformat()

            index += 2
        return row

    def parse_row(self, row):
        """
        Initialize an attestation from a CSV row
        """

        self.complete = row[22]
        self.reviewed = row[23]
        self.file_name = row[24]
        self.web_view_link = row[25]
        for index in range(0, 4):
            name = row[index * 3].strip()
            email = row[index * 3 + 1].strip()
            birthdate = row[index * 3 + 2].strip()
            date = datetime.date.min
            if len(birthdate) > 0:
                date = datetime.date.fromisoformat(birthdate)
            if len(name) > 0:
                self.adults.append(AttestEntry(name, email, date))
        for index in range(0, 5):
            name = row[12 + index * 2].strip()
            birthdate = row[12 + index * 2 + 1].strip()
            date = datetime.date.min
            if len(birthdate) > 0:
                date = datetime.date.fromisoformat(birthdate)
            if len(name) > 0:
                self.minors.append(AttestEntry(name, "", date))


    @staticmethod
    def read_csv(
        attestations_csv_file=attestations_csv_filename,
    ) -> list[Attestation]:
        """
        Read attestations from a CSV file
        """
        result = []
        print(f"Note: reading attestations file '{attestations_csv_file}'")
        if not os.path.exists(attestations_csv_file):
            return result

        with open(attestations_csv_file, "r", newline="") as f:
            reader = csv.reader(f)
            count = 0
            for row in reader:
                count += 1
                if count == 1:
                    continue
                attestation = Attestation()
                attestation.parse_row(row)
                result.append(attestation)
        print(f"Note: read {count} attestations")
        return result

    @staticmethod
    def write_csv(
        attestations: list[Attestation], attestations_csv_file=attestations_csv_filename
    ):
        """
        Write a set of attesttions to a CSV file
        """

        if not csvfile.backup_file(attestations_csv_file):
            return

        print(f"Note: writing attestations file '{attestations_csv_file}'")

        with open(attestations_csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(Attestation.HEADER)
            for attestation in attestations:
                writer.writerow(attestation.get_row())
            f.close()
        print(f"Note: write {len(attestations)} attestation records")

    @staticmethod
    def create_doc_map(attestations: list[Attestation]) -> dict[str, Attestation]:
        doc_map: dict[str, Attestation] = {}
        for attestation in attestations:
            doc_map[attestation.adults[0].name] = attestation
        return doc_map



guestwaiver_csv_filename = "data/guest_waivers.csv"
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
        for i, name in enumerate(self.minors):
            row[GuestWaiver.HEADER[i + 2]] = name
        row[GuestWaiver.FIELD_LINK] = self.web_view_link
        row[GuestWaiver.FIELD_FILENAME] = self.file_name
        row[GuestWaiver.FIELD_DATE] = self.date_signed
        row[GuestWaiver.FIELD_SIGNER] = self.adult_signer
 
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

    @staticmethod
    def key_func(record: GuestWaiver) -> str:
        return Signature.last_name(record.adult_signer)

    @staticmethod
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


    @staticmethod
    def write_csv(waivers: list[GuestWaiver], csv_file: str = guestwaiver_csv_filename):

        if not csvfile.backup_file(csv_file):
            return

        print(f"Note: writing waiver file '{csv_file}'")
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GuestWaiver.HEADER)
            writer.writeheader()
            for waiver in waivers:
                writer.writerow(waiver.get_row())
            f.close()
        print(f"Note: wrote {len(waivers)} guest waiver records.")




def simple_test_member_waiver() -> None:
    filename = "test_member_waivers.csv"

    # Expect an empty file
    waivers: list[MemberWaiver] = MemberWaiver.read_csv(filename)

    # Add records
    waiver = MemberWaiver()
    waiver.signatures.append(Signature("Bob", "2012-01-05"))
    waiver.minors.append("Sam")
    waiver.file_name = "waiver1.pdf"
    waiver.web_view_link = "http://web.com/waiver1.pdf"
    waivers.append(waiver)

    waiver = MemberWaiver()
    waiver.signatures.append(Signature("Erica", "2019-11-15"))
    waiver.signatures.append(Signature("Lionel", "2019-11-15"))
    waiver.minors.append("Parth")
    waiver.file_name = "waiver2.pdf"
    waiver.web_view_link = "http://web.com/waiver2.pdf"
    waivers.append(waiver)

    waiver = MemberWaiver()
    waiver.signatures.append(Signature("Adult1", "2019-11-01"))
    waiver.signatures.append(Signature("Adult2", "2019-11-02"))
    waiver.minors.append("Minor1")
    waiver.minors.append("Minor2")
    waiver.minors.append("Minor3")
    waiver.minors.append("Minor4")
    waiver.file_name = "waiver3.pdf"
    waiver.web_view_link = "http://web.com/waiver3.pdf"
    waivers.append(waiver)

    MemberWaiver.write_csv(waivers, filename)
    waivers = MemberWaiver.read_csv(filename)
    MemberWaiver.write_csv(waivers, filename)
    waivers = MemberWaiver.read_csv(filename)
    os.unlink(filename)
    for name in csvfile.get_backup_filenames(filename):
        if os.path.exists(name):
            os.unlink(name)


def simple_test_attest():

    attest_filename = "test_attestations.csv"
    Attestation.write_csv([], attestations_csv_file=attest_filename)
    attests = Attestation.read_csv(attestations_csv_file=attest_filename)
    assert len(attests) == 0

    attest = Attestation()
    attest.adults.append(
        AttestEntry("Jim", "jim@example.com", datetime.date.fromisoformat("2012-12-12"))
    )
    attest.web_view_link = "http://www.example.com/view1"
    attests.append(attest)

    attest = Attestation()
    attest.adults.append(
        AttestEntry(
            "adult1", "adult1@example.com", datetime.date.fromisoformat("2012-12-01")
        )
    )
    attest.adults.append(
        AttestEntry(
            "adult2", "adult2@example.com", datetime.date.fromisoformat("2012-12-02")
        )
    )
    attest.adults.append(
        AttestEntry(
            "adult3", "adult3@example.com", datetime.date.fromisoformat("2012-12-03")
        )
    )
    attest.adults.append(
        AttestEntry(
            "adult4", "adult4@example.com", datetime.date.fromisoformat("2012-12-04")
        )
    )
    attest.minors.append(
        AttestEntry(
            "minor1", "email1@example.com", datetime.date.fromisoformat("2020-01-01")
        )
    )
    attest.minors.append(
        AttestEntry(
            "minor2", "email2@example.com", datetime.date.fromisoformat("2020-01-02")
        )
    )
    attest.minors.append(
        AttestEntry(
            "minor3", "email3@example.com", datetime.date.fromisoformat("2020-01-03")
        )
    )
    attest.minors.append(
        AttestEntry(
            "minor4", "email4@example.com", datetime.date.fromisoformat("2020-01-04")
        )
    )
    attest.minors.append(
        AttestEntry(
            "minor5", "email5@example.com", datetime.date.fromisoformat("2020-01-05")
        )
    )
    attest.web_view_link = "http://www.example.com/view2"
    attest.file_name = "attest.pdf"
    attests.append(attest)

    Attestation.write_csv(attests, attestations_csv_file=attest_filename)
    attests = Attestation.read_csv(attestations_csv_file=attest_filename)
    assert len(attests) == 2
    os.unlink(attest_filename)
    for name in csvfile.get_backup_filenames(attest_filename):
        if os.path.exists(name):
            os.unlink(name)


def simple_test_guest() -> None:
    waivers: list[GuestWaiver] = []

    waiver_filename: str = "test_guest_waivers.csv"
    # Empty file
    GuestWaiver.write_csv(waivers, waiver_filename)
    GuestWaiver.read_csv()

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
    GuestWaiver.write_csv(waivers, waiver_filename)
    waivers = GuestWaiver.read_csv()
    os.unlink(waiver_filename)
    for name in csvfile.get_backup_filenames(waiver_filename):
        if os.path.exists(name):
            os.unlink(name)


if __name__ == "__main__":
    simple_test_member_waiver()
    simple_test_attest()
    simple_test_guest()
