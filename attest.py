from dataclasses import dataclass
import datetime
import re
import sys
import csv

import pdfplumber

import dateutil

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

def write_attestations_csv(attestations: list[Attestation], attestations_csv_file = attestations_csv_filename):
    """
    Write a set of attesttions to a CSV file
    """
    print(f"Note: writing attestations file '{attestations_csv_file}'")

    with open(attestations_csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(Attestation.HEADER)
        for attestation in attestations:
            writer.writerow(attestation.get_row())
        f.close()
    print(f"Note: write {len(attestations)} attestation records")
 

def simple_test():
    write_attestations_csv([])
    attests = read_attestations_csv()
    assert(len(attests) == 0)

    attest = Attestation()
    attest.adults.append(AttestEntry("Jim", "jim@example.com", datetime.date.fromisoformat("2012-12-12")))
    attest.web_view_link = "http://www.example.com/view1"
    attests.append(attest)

    attest = Attestation()
    attest.adults.append(AttestEntry("adult1", "adult1@example.com", datetime.date.fromisoformat("2012-12-01")))
    attest.adults.append(AttestEntry("adult2", "adult2@example.com", datetime.date.fromisoformat("2012-12-02")))
    attest.adults.append(AttestEntry("adult3", "adult3@example.com", datetime.date.fromisoformat("2012-12-03")))
    attest.adults.append(AttestEntry("adult4", "adult4@example.com", datetime.date.fromisoformat("2012-12-04")))
    attest.minors.append(AttestEntry("minor1", "email1@example.com", datetime.date.fromisoformat("2020-01-01")))
    attest.minors.append(AttestEntry("minor2", "email2@example.com", datetime.date.fromisoformat("2020-01-02")))
    attest.minors.append(AttestEntry("minor3", "email3@example.com", datetime.date.fromisoformat("2020-01-03")))
    attest.minors.append(AttestEntry("minor4", "email4@example.com", datetime.date.fromisoformat("2020-01-04")))
    attest.minors.append(AttestEntry("minor5", "email5@example.com", datetime.date.fromisoformat("2020-01-05")))
    attest.web_view_link = "http://www.example.com/view2"
    attest.file_name = "attest.pdf"
    attests.append(attest)

    write_attestations_csv(attests)
    attests = read_attestations_csv()
    assert(len(attests) == 2)

if __name__ == "__main__":
    simple_test()
