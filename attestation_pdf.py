from dataclasses import dataclass
import sys

import pdfplumber

class Attestation:
    """Data from attestation"""

    def __init__(self):
        self.file_name: str = ""
        self.web_view_link: str = ""
        self.adults: list[str] = []
        self.minors: list[str] = []

    def __str__(self):
        result = f"file: {self.file_name}"
        result += '\nAdults:'
        for adult in self.adults:
            result += '\n\t' + adult
        result += '\nMinors:'
        for minor in self.minors:
            result += '\n\t' + minor
        return result


markers = [
    'Proprietary Member Name:',
    'Adult 2 (if applicable):',
    'Adult 3 (if applicable)',
    'Adult 4 (if applicable)',
    'Minor 1',
    'Minor 2',
    'Minor 4',
    'Minor 4',
    'Minor 5',
]


def parse_attestation(in_file) -> Attestation:
    attestation = Attestation()
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
        if markers[marker] == line.strip():
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


if __name__ == '__main__':
    with open(sys.argv[1], "rb") as f:
        attestation = parse_attestation(f)
        print(attestation)
