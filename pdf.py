import sys

import pdfplumber


def main(filename: str):
    with pdfplumber.open(filename) as pdf:
        for page in pdf.pages:
            text = page.extract_text_simple()
            print(text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: pdf <filename>")
        sys.exit(-1)
    main(sys.argv[1])
