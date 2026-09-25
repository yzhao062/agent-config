#!/usr/bin/env python3
"""Report a PDF figure's text sizes at its intended document width.

Requires PyMuPDF (import pymupdf). This reads the PDF without modifying it.
It does not render PowerPoint or certify editability, legibility, or semantics.
"""

import argparse
import contextlib
import hashlib
import json
import math
import sys
from pathlib import Path


def positive_number(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and greater than zero")
    return number


def inspect_pdf(path, width_mm, page_number=None, min_font_pt=None):
    import pymupdf

    data = Path(path).read_bytes()
    with pymupdf.open(stream=data, filetype="pdf") as document:
        if not document.is_pdf:
            raise ValueError("input is not a PDF")
        if document.needs_pass:
            raise ValueError("encrypted PDFs require an unlocked copy")
        if page_number is None:
            if len(document) != 1:
                raise ValueError("use --page for a PDF with multiple pages")
            page_number = 1
        if not 1 <= page_number <= len(document):
            raise ValueError("--page is outside the PDF page range")
        page = document[page_number - 1]
        scale = width_mm * 72 / 25.4 / page.rect.width
        spans = []
        for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip():
                        spans.append({
                            "text": span["text"],
                            "font": span["font"],
                            "source_font_pt": span["size"],
                            "placed_font_pt": span["size"] * scale,
                        })
        spans.sort(key=lambda span: span["placed_font_pt"])
        below = [span for span in spans if min_font_pt is not None
                 and span["placed_font_pt"] < min_font_pt - 0.001]
        status = "not_requested"
        if min_font_pt is not None:
            status = "unverifiable" if not spans else "below_minimum" if below else "met"
        return {
            "pdf": str(Path(path).resolve()),
            "sha256": hashlib.sha256(data).hexdigest(),
            "page": page_number,
            "page_count": len(document),
            "source_width_pt": page.rect.width,
            "source_height_pt": page.rect.height,
            "placed_width_mm": width_mm,
            "placed_height_mm": width_mm * page.rect.height / page.rect.width,
            "scale": scale,
            "text_span_count": len(spans),
            "image_occurrence_count": len(page.get_image_info()),
            "smallest_text_spans": spans[:10],
            "minimum_placed_font_pt": spans[0]["placed_font_pt"] if spans else None,
            "requested_minimum_pt": min_font_pt,
            "text_threshold_status": status,
            "below_minimum": below,
            "limits": "Extractable PDF text only; outlined, raster, hidden, or clipped labels need visual inspection. Assumes uniform scaling of the whole page, without extra trim. Does not verify PowerPoint editing or manuscript placement.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--width-mm", type=positive_number, required=True)
    parser.add_argument("--page", type=int, help="1-based page; required for multipage input")
    parser.add_argument("--min-font-pt", type=positive_number,
                        help="optional threshold for extractable text, with 0.001 pt tolerance")
    args = parser.parse_args()
    try:
        with contextlib.redirect_stdout(sys.stderr):
            report = inspect_pdf(args.pdf, args.width_mm, args.page, args.min_font_pt)
    except ImportError:
        parser.exit(2, "PyMuPDF is required; use an environment with the pymupdf package.\n")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"Cannot inspect PDF: {error}\n")
    print(json.dumps(report, indent=2))
    return 1 if report["text_threshold_status"] in ("below_minimum", "unverifiable") else 0


if __name__ == "__main__":
    raise SystemExit(main())
