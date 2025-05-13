import re
import sys

import pdfplumber

class GuestWaiverPDF:
    def __init__(self):
        self.adult: str = ""
        self.minors: list[str] = []
        self.date: str = ""

    def __str__(self):
        result = f"Date: {self.date} - by {self.adult}\nMinors:\n"
        for minor in self.minors:
            result += f"\t{minor}"
        return result

            
# Strings in the PDF file to scrape
MARKERS = [
    "Adult Non-Member/Guest:",
    "",
    "Children (under 18):",
    "[Print Name]",
    "[Print Name]",
    "[Print Name]",
]
EXCLUDE_STR="_____________________________"
DATE_STR="The document has been completed."



def parse_waiver_pdf(in_file) -> GuestWaiverPDF:
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
        print(line)
        if marker < len(MARKERS) and MARKERS[marker] == line.strip():
            print(f"found marker {MARKERS[marker]}")
            marker_found = True
            marker += 1
        elif marker_found:
            marker_found = False
            if len(line.strip()) > 0:
                if marker == 2:
                    waiver.adult = line.strip()
                elif marker > 2 and line.strip() != EXCLUDE_STR:
                    waiver.minors.append(line.strip())
        else:
            # Look for DATE_STR
            m = re.search(DATE_STR, line.strip())
            if m is not None:
                print(f"found DATE_STR {m}")
                waiver.date = line[0:m.span()[0]]

    return waiver

if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        waiver_pdf = parse_waiver_pdf(f)
        print(waiver_pdf)
