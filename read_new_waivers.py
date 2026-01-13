"""
Process new waiver files on gdrive and update the waiver records CSV
"""

import sys
import docs
import extract_attest
import extract_members
import extract_guest


upload: bool = False

def main():
    print("Extract information from new documents.")
    print(f"Reading waiver files for year {docs.YEAR}\n")
    extract_members.run(upload)
    extract_attest.run(upload)
    extract_guest.run(upload)

if __name__ == "__main__":
    if "noupload" in sys.argv:
        sys.argv.remove("noupload")
        upload = False
    if len(sys.argv) > 1:
        docs.YEAR = sys.argv[1]
    main()
