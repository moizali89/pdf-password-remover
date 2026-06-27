# PDF Password Remover

A small, **fully local** web app that removes the password from a PDF you already
know the password to. Upload a protected PDF, enter its password, and download a
decrypted copy that opens without any password.

This is a **known-password decryption** tool — *not* a password cracker. There is
no brute-force or recovery of unknown passwords.

> 🔒 **Your files never leave your computer.** The server binds to `127.0.0.1`
> (localhost) only, nothing is written to disk, and no dependency makes network
> calls. When enabled, a strict Content-Security-Policy stops the page from
> contacting anything external.
>
> ✈️ **It works completely offline — you can turn off your Wi-Fi and run it.**

---

## Requirements

- **Python 3.10 or newer** — [download here](https://www.python.org/downloads/).
  - On Windows, check **"Add Python to PATH"** during installation.

That's it. The launch scripts create an isolated environment and install
everything else (Flask, pikepdf, PyYAML) automatically on first run.

---

## Quick Start

Clone the repository, then run the launcher for your platform.

```bash
git clone <repository-url>
cd pdf-password-remover
```

### macOS / Linux

```bash
./run.sh
```

If you get a "permission denied" error, make the script executable first:

```bash
chmod +x run.sh
./run.sh
```

### Windows

Double-click **`run.bat`**, or from a terminal:

```bat
run.bat
```

---

The first launch sets up a virtual environment and downloads dependencies (this
takes a minute). Subsequent launches start instantly.

When it's running, open your browser to:

**http://127.0.0.1:5000**

Drop in a PDF, type the password, and download the unlocked copy. Press
`Ctrl+C` in the terminal to stop the server.

---

## Configuration

Edit `config.yaml` to change behavior. All values are optional — the app falls
back to sensible defaults if the file or any key is missing.

```yaml
server:
  host: 127.0.0.1        # localhost only — do not expose on the network
  port: 5000
  debug: false

uploads:
  max_file_size_mb: 500
  allowed_extensions:
    - pdf

behavior:
  passthrough_unencrypted: true   # if a PDF isn't encrypted, return it unchanged
  output_prefix: "unlocked-"      # output filename = <prefix><original name>

security:
  enable_csp: true                # send Content-Security-Policy: default-src 'self'
```

---

## Supported Encryption

Powered by [pikepdf](https://github.com/pikepdf/pikepdf) (which wraps QPDF):

- RC4 40-bit and 128-bit
- AES-128
- AES-256

---

## Running the Tests

```bash
# macOS / Linux
.venv/bin/python -m pytest backend/tests/ -v

# Windows
.venv\Scripts\python -m pytest backend\tests\ -v
```

---

## Project Structure

```
pdf-password-remover/
├── backend/
│   ├── app.py            # Flask routes, static serving, security headers
│   ├── decryptor.py      # core decrypt logic (pikepdf), typed errors
│   ├── config.py         # loads config.yaml with defaults
│   ├── requirements.txt  # pikepdf, flask, pyyaml
│   └── tests/            # pytest unit + route tests
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── config.yaml           # user-editable configuration
├── run.sh                # launcher (macOS / Linux)
├── run.bat               # launcher (Windows)
└── README.md
```

---

## A Note on Memory Usage

Decryption happens entirely in memory. A single large job (up to the 500 MB cap)
may transiently use roughly **1–1.5 GB of RAM** (input + working copy + output).
This is fine for local, single-user use. Lower `max_file_size_mb` in
`config.yaml` if your machine has limited memory.

---

## License

Personal use. Provided as-is, without warranty.
