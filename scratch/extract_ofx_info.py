import pypdf
import os

pdf_path = r"e:\Projetos Python\ContaPaga\DOCS\ofx\OFX Banking Specification v2.3.pdf"
output_path = r"e:\Projetos Python\ContaPaga\scratch\ofx_spec_toc.txt"

def extract_toc_and_keywords(path, out_path):
    try:
        reader = pypdf.PdfReader(path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Total Pages: {len(reader.pages)}\n\n")
            f.write("--- TABLE OF CONTENTS / FIRST 30 PAGES ---\n")
            for i in range(min(30, len(reader.pages))):
                text = reader.pages[i].extract_text()
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(text)
                f.write("\n\n")
            
            f.write("--- KEYWORD SEARCH ---\n")
            keywords = ["CREDIT CARD", "CCSTMT", "STMTTRN", "BANKTRAN", "INVOICE"]
            for i in range(len(reader.pages)):
                text = reader.pages[i].extract_text().upper()
                for kw in keywords:
                    if kw in text:
                        f.write(f"Keyword '{kw}' found on page {i+1}\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_toc_and_keywords(pdf_path, output_path)
