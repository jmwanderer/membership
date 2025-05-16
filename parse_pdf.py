"""
Parse Guest PDF waivers

Extract signer's name, list of minor age persons, and date completed.
"""

import io
import re
import sys
from dataclasses import dataclass

import pdfplumber

import attest
import dateutil


@dataclass
class Signature:
    name: str
    date: str


class MemberWaiverPDF:
    def __init__(self) -> None:
        self.signatures: list[Signature] = []
        self.minors: list[str] = []

    def __str__(self) -> str:
        result = "Waiver:"
        for signature in self.signatures:
            result += f"\n\t{signature.name}, {signature.date}"
        for minor in self.minors:
            result += f"\n\t{minor}"
        return result


def parse_member_waiver_pdf(infile: io.BufferedReader | io.BytesIO) -> MemberWaiverPDF:
    """
    Read a member waiver PDF and specific key data.
    """
    waiver = MemberWaiverPDF()
    with pdfplumber.open(infile) as pdf:
        if len(pdf.pages) < 2:
            return waiver
        page = pdf.pages[1]

        # 1st signature
        cpage = page.crop((66, 162, 240, 166))
        name = cpage.extract_text_simple().strip()
        cpage = page.crop((93, 230, 230, 233))
        date = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.signatures.append(Signature(name, date))

        # 2nd signature
        cpage = page.crop((320, 158, 500, 165))
        name = cpage.extract_text_simple().strip()
        cpage = page.crop((344, 230, 465, 231))
        date = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.signatures.append(Signature(name, date))

        # Minors
        # 1
        cpage = page.crop((57, 419, 180, 425))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # 2
        cpage = page.crop((57, 452, 180, 457))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # 3
        cpage = page.crop((57, 485, 180, 490))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # 4
        cpage = page.crop((57, 518, 180, 522))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # child 5
        cpage = page.crop((57, 558, 180, 562))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # child 6
        cpage = page.crop((209, 424, 333, 428))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # child 7
        cpage = page.crop((210, 484, 330, 488))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # child 8
        cpage = page.crop((210, 452, 330, 457))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)

        # child 9
        cpage = page.crop((210, 517, 330, 521))
        name = cpage.extract_text_simple().strip()
        if len(name) > 0:
            waiver.minors.append(name)






    return waiver


class GuestWaiverPDF:
    def __init__(self) -> None:
        self.adult: str = ""
        self.minors: list[str] = []
        self.date: str = ""

    def __str__(self) -> str:
        result = f"Date: {self.date} - by {self.adult}\nMinors:"
        for minor in self.minors:
            result += f"\n\t{minor}"
        return result


# Strings in the PDF file to scrape
GUEST_MARKERS = [
    "Adult Non-Member/Guest:",
    "",
    "Children (under 18):",
    "[Print Name]",
    "[Print Name]",
    "[Print Name]",
]
GUEST_EXCLUDE_STR = "_____________________________"
GUEST_DATE_STR = "The document has been completed."


def parse_guest_waiver_pdf(in_file: io.BufferedReader | io.BytesIO) -> GuestWaiverPDF:
    """
    Read a PDF file and extract specific lines

    """
    waiver = GuestWaiverPDF()
    lines = []
    with pdfplumber.open(in_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text_simple()
            lines.extend(text.split("\n"))

    marker = 0
    marker_found = False
    adult = True

    for line in lines:
        # print(line)
        if marker < len(GUEST_MARKERS) and GUEST_MARKERS[marker] == line.strip():
            # print(f"found marker {GUEST_MARKERS[marker]}")
            marker_found = True
            marker += 1
        elif marker_found:
            marker_found = False
            if len(line.strip()) > 0:
                if marker == 2:
                    waiver.adult = line.strip()
                elif marker > 2 and line.strip() != GUEST_EXCLUDE_STR:
                    waiver.minors.append(line.strip())
        else:
            # Look for DATE_STR
            m = re.search(GUEST_DATE_STR, line.strip())
            if m is not None:
                # print(f"found GUEST_DATE_STR {m}")
                waiver.date = line[0 : m.span()[0]]

    return waiver


class AttestationPDF:
    """Data from attestation PDF file
    Constains knowledge on how to extract information from lines in a PDF
    """

    def __init__(self) -> None:
        self.file_name: str = ""
        self.web_view_link: str = ""
        self.adults: list[str] = []
        self.minors: list[str] = []

    def __str__(self) -> str:
        result = f"file: {self.file_name}"
        result += "\nAdults:"
        for adult in self.adults:
            result += "\n\t" + adult
        result += "\nMinors:"
        for minor in self.minors:
            result += "\n\t" + minor
        return result

    def parse_attestation(self) -> attest.Attestation:
        """
        Parse lines from the PDF file and return an Attestation class
        """
        result = attest.Attestation()
        result.file_name = self.file_name
        result.web_view_link = self.web_view_link
        for entry in self._getAdultMemberEntries():
            result.adults.append(entry)
        for entry in self._getMinorMemberEntries():
            result.minors.append(entry)
        return result

    def _getAdultMemberEntries(self) -> list[attest.AttestEntry]:
        result: list[attest.AttestEntry] = []

        for line in self.adults:
            result.append(AttestationPDF._parseAdult(line))
        return result

    def _getMinorMemberEntries(self) -> list[attest.AttestEntry]:
        result: list[attest.AttestEntry] = []

        for line in self.minors:
            result.append(AttestationPDF._parseMinor(line))
        return result

    @staticmethod
    def _parseAdult(line: str) -> attest.AttestEntry:
        # Look for an email address
        m = re.search(r"\S+@\S+", line)
        if m:
            email = m.group(0)
            name = line[0 : m.span()[0]]
            _, birthdate = dateutil.find_date(line[m.span()[1] :])
        else:
            start, birthdate = dateutil.find_date(line)
            name = line[0:start]
            email = ""

        return attest.AttestEntry(name.strip(), email.strip(), birthdate)

    @staticmethod
    def _parseMinor(line: str) -> attest.AttestEntry:
        start, birthdate = dateutil.find_date(line)
        name = line[0:start]
        return attest.AttestEntry(name.strip(), "", birthdate)


# Strings in the PDF file to scrape
markers = [
    "Proprietary Member Name:",
    "Adult 2 (if applicable):",
    "Adult 3 (if applicable)",
    "Adult 4 (if applicable)",
    "Minor 1",
    "Minor 2",
    "Minor 3",
    "Minor 4",
    "Minor 5",
]


def parse_attestation_pdf(in_file: io.BufferedReader | io.BytesIO) -> AttestationPDF:
    """
    Read a PDF file and extract specific lines

    Note: mostly works. Will fail when values wrap to two lines.
    """
    attestation = AttestationPDF()
    lines = []
    with pdfplumber.open(in_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text_simple()
            lines.extend(text.split("\n"))

    marker = 0
    marker_found = False
    adult = True

    for line in lines:
        # print(line)
        if marker < len(markers) and markers[marker] == line.strip():
            # print(f"found marker {markers[marker]}")
            marker_found = True
            if marker > 3:
                adult = False
            marker += 1
        elif marker_found:
            marker_found = False
            if len(line.strip()) > 0:
                if adult:
                    attestation.adults.append(line.strip())
                else:
                    attestation.minors.append(line.strip())

    return attestation


if __name__ == "__main__":
    options = ["member", "guest", "attest"]
    if len(sys.argv) != 3 or sys.argv[1] not in options:
        print(f"Usage parse_pdf {options} <filename>")
        sys.exit(-1)
    with open(sys.argv[2], "rb") as f:
        if sys.argv[1] == "guest":
            guest_waiver_pdf = parse_guest_waiver_pdf(f)
            print(guest_waiver_pdf)
        elif sys.argv[1] == "attest":
            attestation_pdf = parse_attestation_pdf(f)
            print(attestation_pdf)
            attestation = attestation_pdf.parse_attestation()
            print(attestation)
        else:
            member_waiver_pdf = parse_member_waiver_pdf(f)
            print(member_waiver_pdf)
