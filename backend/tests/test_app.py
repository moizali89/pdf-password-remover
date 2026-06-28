import pikepdf
import pytest
from io import BytesIO

from backend.app import app as flask_app


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


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_happy_path_returns_pdf(client):
    pdf_bytes = _make_encrypted_pdf("pass123")
    data = {"file": (BytesIO(pdf_bytes), "test.pdf"), "password": "pass123"}
    resp = client.post("/api/unlock", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"
    assert b"unlocked-test.pdf" in resp.headers["Content-Disposition"].encode()


def test_wrong_password_returns_401(client):
    pdf_bytes = _make_encrypted_pdf("correct")
    data = {"file": (BytesIO(pdf_bytes), "test.pdf"), "password": "wrong"}
    resp = client.post("/api/unlock", data=data, content_type="multipart/form-data")
    assert resp.status_code == 401
    assert "Incorrect password" in resp.json["error"]


def test_no_file_returns_400(client):
    resp = client.post("/api/unlock", data={"password": "x"}, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_non_pdf_extension_returns_400(client):
    data = {"file": (BytesIO(b"hello"), "doc.txt"), "password": ""}
    resp = client.post("/api/unlock", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "PDF" in resp.json["error"]


def test_corrupt_pdf_returns_400(client):
    data = {"file": (BytesIO(b"not a pdf"), "fake.pdf"), "password": ""}
    resp = client.post("/api/unlock", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_unencrypted_pdf_passthrough(client):
    pdf_bytes = _make_plain_pdf()
    data = {"file": (BytesIO(pdf_bytes), "plain.pdf"), "password": ""}
    resp = client.post("/api/unlock", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"html" in resp.data.lower()


def test_config_endpoint_returns_min_loader_seconds(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    assert isinstance(resp.json["min_loader_seconds"], (int, float))
