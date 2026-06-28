import os
import re
from io import BytesIO

from flask import Flask, jsonify, request, send_file, send_from_directory

from backend.config import load_config
from backend.decryptor import InvalidPDF, NotEncrypted, WrongPassword, decrypt

CONFIG = load_config()

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = CONFIG["uploads"]["max_file_size_mb"] * 1024 * 1024

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.after_request
def set_security_headers(response):
    if CONFIG["security"]["enable_csp"]:
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/css/<path:filename>")
def css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), filename)


@app.route("/api/config")
def client_config():
    return jsonify({"min_loader_seconds": CONFIG["ui"]["min_loader_seconds"]})


@app.errorhandler(413)
def too_large(_):
    max_mb = CONFIG["uploads"]["max_file_size_mb"]
    return jsonify({"error": f"File exceeds the {max_mb} MB limit."}), 413


def _sanitize_filename(name: str) -> str:
    name = os.path.basename(name)
    name = re.sub(r"[^\w\-_. ]", "_", name)
    return name or "file.pdf"


@app.route("/api/unlock", methods=["POST"])
def unlock():
    allowed_ext = CONFIG["uploads"]["allowed_extensions"]

    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "Please choose a PDF file."}), 400

    uploaded = request.files["file"]
    original_name = _sanitize_filename(uploaded.filename)

    if not any(original_name.lower().endswith(f".{ext}") for ext in allowed_ext):
        return jsonify({"error": "Please choose a PDF file."}), 400

    password = request.form.get("password", "")
    pdf_bytes = uploaded.read()

    passthrough = CONFIG["behavior"]["passthrough_unencrypted"]
    prefix = CONFIG["behavior"]["output_prefix"]

    try:
        result_bytes = decrypt(pdf_bytes, password, passthrough_unencrypted=passthrough)
    except WrongPassword:
        return jsonify({"error": "Incorrect password — please try again."}), 401
    except InvalidPDF:
        return jsonify({"error": "This doesn't look like a valid PDF."}), 400
    except NotEncrypted:
        return jsonify({"error": "This PDF is not password-protected."}), 400

    output_name = f"{prefix}{original_name}"
    return send_file(
        BytesIO(result_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=output_name,
    )


if __name__ == "__main__":
    app.run(
        host=CONFIG["server"]["host"],
        port=CONFIG["server"]["port"],
        debug=CONFIG["server"]["debug"],
    )
