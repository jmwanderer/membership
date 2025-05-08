from dataclasses import dataclass
import datetime
import re
import sys
import csv

import pdfplumber

attestations_csv_filename = "output/attestations.csv"

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

    def __init__(self):
        self.file_name: str = ""
        self.web_view_link: str = ""
        self.adults: list[AttestEntry] = []
        self.minors: list[AttestEntry] = []

    def __str__(self):
        result = self.file_name
        result += "\n\t" + self.web_view_link
        for adult in self.adults:
            result += "\n\t" + str(adult)
        for minor in self.minors:
            result += "\n\t" + str(minor)

        return result
        

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
    FIELD_ADULT4_BIRTHDATE = "adult1_birthdate"
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
    FIELD_LINK = "link"
    FIELD_NAME = "name"

    HEADER = [ FIELD_ADULT1, FIELD_ADULT1_EMAIL, FIELD_ADULT1_BIRTHDATE,
               FIELD_ADULT2, FIELD_ADULT2_EMAIL, FIELD_ADULT2_BIRTHDATE,
               FIELD_ADULT3, FIELD_ADULT3_EMAIL, FIELD_ADULT3_BIRTHDATE,
               FIELD_ADULT4, FIELD_ADULT4_EMAIL, FIELD_ADULT4_BIRTHDATE,
               FIELD_MINOR1, FIELD_MINOR1_BIRTHDATE,
               FIELD_MINOR2, FIELD_MINOR2_BIRTHDATE,
               FIELD_MINOR3, FIELD_MINOR3_BIRTHDATE,
               FIELD_MINOR4, FIELD_MINOR4_BIRTHDATE,
               FIELD_MINOR5, FIELD_MINOR5_BIRTHDATE,
               FIELD_LINK,
               FIELD_NAME ]

    def get_row(self):
        """
        Generate a CSV row for this attestation
        """
        row = [ '' ] * 24
        row[22] = self.file_name
        row[23] = self.web_view_link

        index = 0
        for adult in self.adults:
            row[index] = adult.name
            row[index + 1] = adult.email
            if adult.birthdate != datetime.date.min:
                row[index + 2 ] = adult.birthdate.isoformat()
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

        self.file_name = row[22]
        self.web_view_link = row[23]
        for index in range(0,4):
            name = row[index * 3].strip()
            email = row[index * 3 + 1].strip()
            birthdate = row[index * 3 + 2].strip()
            if len(birthdate) > 0:
                date = datetime.date.fromisoformat(birthdate)
            date = datetime.date.min
            if len(name) > 0:
                self.adults.append(AttestEntry(name, email, date))
        for index in range(0,5):
            name = row[12 + index * 2].strip()
            birthdate = row[12 + index * 2 + 1].strip()
            date = datetime.date.min
            if len(birthdate) > 0:
                date = datetime.date.fromisoformat(birthdate)
            if len(name) > 0:
                self.minors.append(AttestEntry(name, '', date))

def read_attestations_csv(attestations_csv_file = attestations_csv_filename) -> list[Attestation]:
    """
    Read attestations from a CSV file
    """ 
    result = []
    print(f"Note: reading attestations file '{attestations_csv_file}'")

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



class AttestationPDF:
    """Data from attestation PDF file
       Constains knowledge on how to extract information from lines in a PDF
    """

    def __init__(self):
        self.file_name: str = ""
        self.web_view_link: str = ""
        self.adults: list[str] = []
        self.minors: list[str] = []

    def __str__(self):
        result = f"file: {self.file_name}"
        result += "\nAdults:"
        for adult in self.adults:
            result += "\n\t" + adult
        result += "\nMinors:"
        for minor in self.minors:
            result += "\n\t" + minor
        return result

    def parse_attestation(self) -> Attestation:
        """
        Parse lines from the PDF file and return an Attestation class
        """
        result = Attestation()
        result.file_name = self.file_name
        result.web_view_link = self.web_view_link
        for entry in self._getAdultMemberEntries():
            result.adults.append(entry)
        for entry in self._getMinorMemberEntries():
            result.minors.append(entry)
        return result

    def _getAdultMemberEntries(self) -> list[AttestEntry]:
        result: list[AttestEntry] = []

        for line in self.adults:
            result.append(AttestationPDF._parseAdult(line))
        return result
                
    def _getMinorMemberEntries(self) -> list[AttestEntry]:
        result: list[AttestEntry] = []

        for line in self.minors:
            result.append(AttestationPDF._parseMinor(line))
        return result

    def _parseAdult(line: str) -> AttestEntry:
        # Look for an email address
        m = re.search(r'\S+@\S+', line)
        if m:
            email = m.group(0)
            name = line[0 : m.span()[0]]
            _, birthdate = find_date(line[m.span()[1]:])
        else:
            start, birthdate = find_date(line)
            name = line[0:start]
            email = ''

        return AttestEntry(name.strip(), email.strip(), birthdate)

    def _parseMinor(line: str) -> AttestEntry:
        start, birthdate = find_date(line)
        name = line[0:start]
        return AttestEntry(name.strip(), '', birthdate)

MONTHS = [ "january", "february", "march", "april", "may", "june",
           "july", "august", "september", "october", "november", "december" ]
ABV1_MONTHS = [ "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sept", "oct", "nov", "dec" ]
ABV2_MONTHS = [ "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec" ]



def lookup_month(month: str) -> int:
    month = month.lower()
    if month in MONTHS:
        return MONTHS.index(month) + 1
    if month in ABV1_MONTHS:
        return ABV1_MONTHS.index(month) + 1
    if month in ABV2_MONTHS:
        return ABV2_MONTHS.index(month) + 1
    return 0
    

def find_date(line: str) -> tuple[int, datetime.date]:
    """
    Search for a state in the line str.
    Return the starting point of the date in the string and
    a date in standard format.
    """
    # TODO: consider handling spaces:  XX XX XXXX
    month = 0
    day = 0
    year = 0
    start = len(line)

    m = re.search(r'(\d+)/(\d+)/(\d+)', line) 
    if m is None:
        m = re.search(r'(\d+)-(\d+)-(\d+)', line)
    if m is None:
        m = re.search(r'(\d\d)(\d\d)(\d+)', line)
    if m is None:
        m = re.search(r'(\d\d)\.(\d\d)\.(\d+)', line)

    if m is not None:
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        start = m.span()[0]

    if m is None:
        # Try month / year
        m = re.search(r'(\d+)/(\d+)', line) 
        if m is not None:
            month = int(m.group(1))
            day = 1
            year = int(m.group(2))
 
    if m is None:
        # Try Month Day, Year or Month Day Year
        m = re.search(r'(\w+)\.?\s+(\d+),?\s+(\d+)', line)
        if m is not None:
            month = lookup_month(m.group(1))
            if month != 0:
                day = int(m.group(2))
                year = int(m.group(3))
                start = m.span()[0]
            else:
                print(f"month lookup failed {m.group(1)}")
                m = None

    if m is None:
        # Try Day Month Year
        m = re.search(r'(\d+)\s+(\w+)\.?\s+(\d+)', line)
        if m is not None:
            month = lookup_month(m.group(2))
            if month != 0:
                day = int(m.group(1))
                year = int(m.group(3))
                start = m.span()[0]
            else:
                m = None

    if m is None:
        # Try just Year
        m = re.search(r'(\d+)\Z', line)
        if m is not None:
            year = int(m.group(1))
            day = 1
            month = 1
            start = m.span()[0]
 
    date = datetime.date.min

    if year < 1900:
        # TODO: fix this check
        if year > 26:
            year += 1900
        else:
            year += 2000

    try:
        if start < len(line):
            date = datetime.date(year, month, day)
    except ValueError:
        pass
    return (start, date)

        
            
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


def parse_attestation_pdf(in_file) -> AttestationPDF:
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
        #print(line)
        if marker < len(markers) and markers[marker] == line.strip():
            #print(f"found marker {markers[marker]}")
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
    with open(sys.argv[1], "rb") as f:
        attestation_pdf = parse_attestation_pdf(f)
        print(attestation_pdf)
        attestation = attestation_pdf.parse_attestation()
        print(attestation)
