#!/usr/bin/env python3
"""
resize_pdf.py

Scales every page of input.pdf to letter size (8.5×11 in).
Usage: python resize_pdf.py input.pdf output.pdf
"""

import sys
from pypdf import PdfReader, PdfWriter

# Letter size in PDF points (72 pt = 1 inch)
LETTER_WIDTH  = 8.5 * 72   # 612
LETTER_HEIGHT = 11  * 72   # 792

def resize_to_letter(in_path: str, out_path: str):
    reader = PdfReader(in_path)
    writer = PdfWriter()

    for page in reader.pages:
        # Scale the existing page content to fit exactly 8.5×11"
        page.scale_to(LETTER_WIDTH, LETTER_HEIGHT)
        # Also reset the media box so Acrobat sees the new page size
        page.mediabox.upper_right = (LETTER_WIDTH, LETTER_HEIGHT)
        writer.add_page(page)

    with open(out_path, "wb") as f:
        writer.write(f)
    print(f"Written resized PDF to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python resize_pdf.py input.pdf output.pdf")
        sys.exit(1)
    resize_to_letter(sys.argv[1], sys.argv[2])
