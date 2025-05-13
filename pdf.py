import pdfplumber

def main():
    with pdfplumber.open("guest.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text_simple()
            print(text)

if __name__ == "__main__":
    main()


