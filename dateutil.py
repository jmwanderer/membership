"""
Utility for handling dates in various formats
"""

import re
import datetime


# TODO: consider consolidating these. In particular, we don't need ABV1 and ABV2
MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
ABV1_MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sept",
    "oct",
    "nov",
    "dec",
]
ABV2_MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def _lookup_month(month: str) -> int:
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

    m = re.search(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", line)
    if m is None:
        m = re.search(r"(\d+)-(\d+)-(\d+)", line)
    if m is None:
        m = re.search(r"(\d\d)(\d\d)(\d+)", line)
    if m is None:
        m = re.search(r"(\d\d)\.(\d\d)\.(\d+)", line)

    if m is not None:
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        start = m.span()[0]

    if m is None:
        # Try month / year
        m = re.search(r"(\d+)/(\d+)", line)
        if m is not None:
            month = int(m.group(1))
            day = 1
            year = int(m.group(2))

    if m is None:
        # Try Month Day, Year or Month Day Year
        m = re.search(r"(\w+)\.?\s+(\d+),?\s+(\d+)", line)
        if m is not None:
            month = _lookup_month(m.group(1))
            if month != 0:
                day = int(m.group(2))
                year = int(m.group(3))
                start = m.span()[0]
            else:
                print(f"month lookup failed {m.group(1)}")
                m = None

    if m is None:
        # Try Day Month Year
        m = re.search(r"(\d+)\s+(\w+)\.?\s+(\d+)", line)
        if m is not None:
            month = _lookup_month(m.group(2))
            if month != 0:
                day = int(m.group(1))
                year = int(m.group(3))
                start = m.span()[0]
            else:
                m = None

    if m is None:
        # Try just Year
        m = re.search(r"(\d+)\Z", line)
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


def simple_test():
    print("Testing dateutil.find_date")
    s, d = find_date("djdjdjdj 1/1/2002")
    assert d != datetime.date.min
    assert s == 9
    _, d = find_date("05 / 12 / 2025")
    assert d != datetime.date.min
    _, d = find_date("05 / 12 / 2025 - by Jim Wanderer")
    assert d != datetime.date.min
    _, d = find_date("")
    assert d == datetime.date.min


if __name__ == "__main__":
    simple_test()
