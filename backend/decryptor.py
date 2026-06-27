import pikepdf
from io import BytesIO


class WrongPassword(Exception):
    pass


class NotEncrypted(Exception):
    pass


class InvalidPDF(Exception):
    pass


def decrypt(pdf_bytes: bytes, password: str, *, passthrough_unencrypted: bool = True) -> bytes:
    try:
        pdf = pikepdf.open(BytesIO(pdf_bytes), password=password)
    except pikepdf.PasswordError:
        raise WrongPassword("Incorrect password")
    except pikepdf.PdfError:
        raise InvalidPDF("Not a valid PDF or file is corrupt")
    except Exception as e:
        raise InvalidPDF(f"Could not open PDF: {e}")

    with pdf:
        if not pdf.is_encrypted:
            if passthrough_unencrypted:
                return pdf_bytes
            raise NotEncrypted("PDF is not encrypted")

        out = BytesIO()
        pdf.save(out)
        return out.getvalue()
