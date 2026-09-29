"""Tool: read_document

Reads a source document (FRD, spec, screen description, etc.) and returns
plain text. Supports .txt, .md, .docx, .pdf.
"""
from pathlib import Path


def read_document(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input document not found: {path}")

    suffix = p.suffix.lower()

    if suffix in (".txt", ".md"):
        return p.read_text(encoding="utf-8")

    if suffix == ".docx":
        from docx import Document

        doc = Document(str(p))
        parts = [para.text for para in doc.paragraphs if para.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    raise ValueError(f"Unsupported document type: {suffix}")
