"""Validating PDFs and extracting their text."""

import hashlib

import pymupdf

PDF_SIGNATURE = b"%PDF-"


class InvalidPDF(ValueError):
    """The upload is not a usable PDF. The message is safe to show to users."""


def validate_pdf(data: bytes, max_bytes: int) -> None:
    if not data:
        raise InvalidPDF("The file is empty.")
    if len(data) > max_bytes:
        raise InvalidPDF(f"The file is too large. The limit is {max_bytes // (1024 * 1024)} MB.")
    if not data[:1024].lstrip().startswith(PDF_SIGNATURE):
        raise InvalidPDF("Only PDF files are supported.")


def extract_text(data: bytes) -> str:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise InvalidPDF("Password-protected PDFs aren't supported.")
            # Pages are separated by a form feed, so passages can cite the page they come from
            text = "\f".join(page.get_text().replace("\f", "\n") for page in doc)
    except InvalidPDF:
        raise
    except Exception as e:
        raise InvalidPDF("This PDF couldn't be read. It may be damaged.") from e
    if not text.strip():
        raise InvalidPDF("No text was found in this PDF. Scanned PDFs aren't supported yet.")
    return text


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
