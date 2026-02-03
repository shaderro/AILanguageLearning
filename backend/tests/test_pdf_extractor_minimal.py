from __future__ import annotations

import io

from backend.preprocessing.pdf_extractor import extract_text_from_pdf_bytes


def build_min_pdf(text: str) -> bytes:
    """
    Build a minimal, valid PDF with a single page containing `text`.
    This is only for smoke-testing extraction; not intended for production usage.
    """

    objects: list[str] = []

    def add_obj(body: str) -> int:
        objects.append(body)
        return len(objects)

    # 1: catalog, 2: pages, 3: page, 4: contents, 5: font
    add_obj("<< /Type /Catalog /Pages 2 0 R >>")
    add_obj("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    add_obj(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )

    # Escape parentheses/backslash for PDF string literal
    pdf_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 24 Tf 72 72 Td ({pdf_text}) Tj ET".encode("latin-1")
    add_obj("<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream.decode("latin-1")))
    add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")

    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode("ascii"))
        out.write(body.encode("latin-1"))
        out.write(b"\nendobj\n")

    xref_pos = out.tell()
    out.write(b"xref\n")
    out.write(f"0 {len(objects) + 1}\n".encode("ascii"))
    out.write(b"0000000000 65535 f \n")
    for i in range(1, len(objects) + 1):
        out.write(f"{offsets[i]:010d} 00000 n \n".encode("ascii"))

    out.write(b"trailer\n")
    out.write(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii"))
    out.write(b"startxref\n")
    out.write(f"{xref_pos}\n".encode("ascii"))
    out.write(b"%%EOF\n")
    return out.getvalue()


def test_pdf_extractor_smoke() -> None:
    pdf_bytes = build_min_pdf("Hello PDF")
    extracted = extract_text_from_pdf_bytes(pdf_bytes)
    assert "Hello PDF" in extracted

