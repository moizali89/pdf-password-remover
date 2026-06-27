import pikepdf
import pytest
from io import BytesIO

from backend.decryptor import decrypt, WrongPassword, NotEncrypted, InvalidPDF


def _make_encrypted_pdf(password: str) -> bytes:
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    out = BytesIO()
    pdf.save(out, encryption=pikepdf.Encryption(owner=password, user=password, R=6))
    return out.getvalue()


def _make_plain_pdf() -> bytes:
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    out = BytesIO()
    pdf.save(out)
    return out.getvalue()


def test_correct_password_returns_decrypted_bytes():
    pdf_bytes = _make_encrypted_pdf("secret")
    result = decrypt(pdf_bytes, "secret")
    opened = pikepdf.open(BytesIO(result))
    assert not opened.is_encrypted


def test_wrong_password_raises():
    pdf_bytes = _make_encrypted_pdf("secret")
    with pytest.raises(WrongPassword):
        decrypt(pdf_bytes, "wrong")


def test_unencrypted_passthrough_true_returns_input():
    pdf_bytes = _make_plain_pdf()
    result = decrypt(pdf_bytes, "", passthrough_unencrypted=True)
    assert result == pdf_bytes


def test_unencrypted_passthrough_false_raises():
    pdf_bytes = _make_plain_pdf()
    with pytest.raises(NotEncrypted):
        decrypt(pdf_bytes, "", passthrough_unencrypted=False)


def test_garbage_bytes_raises_invalid_pdf():
    with pytest.raises(InvalidPDF):
        decrypt(b"not a pdf at all", "")


def test_empty_bytes_raises_invalid_pdf():
    with pytest.raises(InvalidPDF):
        decrypt(b"", "")
