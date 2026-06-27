# PDF Password Remover — Design Spec

**Date:** 2026-06-27
**Status:** Approved design, pending implementation plan

## Summary

A **personal, local web application** that removes the password from a PDF the
user already knows the password to. The user uploads a PDF, enters its password,
and downloads a decrypted copy that opens without any password.

This is a *known-password decryption* tool — **not** a password cracker. There is
no brute-force/recovery functionality.

## Goals

- Decrypt a password-protected PDF using the **known** password and return a
  PDF that opens with no password.
- Polished, iLovePDF-style web UI: drag-and-drop, clear states, prominent
  download button.
- Runs entirely **locally and offline**. No uploaded data ever leaves the
  user's computer; no dependency contacts the internet.
- Configurable via a YAML file.

## Non-Goals (YAGNI)

- No password cracking / brute-force / recovery of unknown passwords.
- No user accounts, authentication, sessions, or database.
- No persistence — files are never written to disk.
- No batch/folder processing (single file per request).
- No public-internet deployment or multi-user hardening.
- No removal of *owner-only* permission restrictions as a separate feature
  (decrypting with the known password already produces an unrestricted PDF).

## Language & Stack

- **Language:** Python 3
- **PDF engine:** `pikepdf` (wraps QPDF; handles RC4 40/128-bit, AES-128,
  AES-256). Pure-local C++ engine, no network use.
- **Web framework:** `Flask`
- **Config parsing:** `PyYAML` (`yaml.safe_load`)
- **Testing:** `pytest`

All four dependencies operate fully offline. No CDN, telemetry, or network I/O.

## Architecture

Single-process Flask app, three independently testable layers:

1. **Core decryptor** (`backend/decryptor.py`) — pure function with no web
   knowledge. Input: PDF bytes + password (+ behavior flags). Output: decrypted
   PDF bytes. Raises typed errors. This is the only module that imports pikepdf.
2. **Config loader** (`backend/config.py`) — loads `config.yaml` with built-in
   defaults; missing file or missing keys fall back to defaults.
3. **Web layer** (`backend/app.py`) — Flask routes. Serves the static frontend,
   exposes one API endpoint, translates core errors into JSON responses, sets
   security headers.

The **frontend** (`frontend/`) is pure static assets (HTML/CSS/vanilla JS),
served by Flask. It performs the upload via `fetch`, receives the decrypted PDF
as a blob, and presents a result screen with a download button.

## Project Structure

```
pdf-password-remover/
├── backend/
│   ├── app.py                 # Flask routes + static serving + security headers
│   ├── decryptor.py           # core decrypt logic (pikepdf), typed errors
│   ├── config.py              # loads config.yaml with defaults
│   ├── requirements.txt       # pikepdf, flask, pyyaml, pytest
│   └── tests/
│       ├── test_decryptor.py  # core unit tests
│       └── test_app.py        # Flask route tests (test client)
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── config.yaml                # user-editable configuration
├── run.sh                     # convenience launcher
└── README.md
```

## Configuration (`config.yaml`)

```yaml
server:
  host: 127.0.0.1        # localhost only — never expose on the network
  port: 5000
  debug: false

uploads:
  max_file_size_mb: 500
  allowed_extensions:
    - pdf

behavior:
  passthrough_unencrypted: true   # if PDF isn't encrypted, return it unchanged
  output_prefix: "unlocked-"      # output filename = <prefix><original name>

security:
  enable_csp: true                # send Content-Security-Policy: default-src 'self'
```

`backend/config.py` defines a matching set of defaults so the app runs even if
`config.yaml` is absent or partial.

## Data Flow

1. Browser loads `/` → static frontend.
2. User selects/drops a PDF and types the password.
3. Frontend `POST /api/unlock` with multipart form: `file` + `password`.
4. Flask rejects early if `Content-Length` exceeds the configured cap.
5. Web layer reads bytes into memory (`BytesIO`), calls the core decryptor.
6. Core opens with pikepdf using the password, saves a decrypted copy to a
   `BytesIO`, returns the bytes.
7. Flask streams the bytes back with
   `Content-Disposition: attachment; filename="<prefix><name>.pdf"`.
8. Frontend turns the response into a blob URL and shows the download button.
9. Request ends; all in-memory bytes are released. Nothing persisted.

## API

### `GET /`
Serves `frontend/index.html`.

### `GET /static/...`
Serves frontend CSS/JS assets.

### `POST /api/unlock`
**Request:** `multipart/form-data` with:
- `file`: the PDF
- `password`: string (may be empty)

**Success (200):** body = decrypted PDF bytes,
`Content-Type: application/pdf`,
`Content-Disposition: attachment; filename="unlocked-<name>.pdf"`.

**Error (4xx):** JSON `{ "error": "<human-readable message>" }`:
- `400` — no file provided / not a `.pdf` / corrupt or invalid PDF.
- `401` — incorrect password.
- `413` — file exceeds `max_file_size_mb`.

## Core Decryptor Behavior

`decrypt(pdf_bytes, password, *, passthrough_unencrypted) -> bytes`

- **Encrypted + correct password** → returns decrypted PDF bytes.
- **Encrypted + wrong password** → raises `WrongPassword`.
- **Not encrypted** → if `passthrough_unencrypted` is true, return input
  unchanged; otherwise raise `NotEncrypted`.
- **Not a valid PDF / corrupt** → raises `InvalidPDF`.

Typed exceptions (e.g. `WrongPassword`, `NotEncrypted`, `InvalidPDF`) live in
`decryptor.py` and are mapped to HTTP responses by the web layer.

## Security & Privacy

- **Localhost binding:** server binds to `127.0.0.1` only. Not reachable from
  other devices.
- **No disk persistence:** uploaded and decrypted bytes live only in memory for
  the request lifetime.
- **Offline by construction:** no dependency makes network calls; the frontend
  bundles all assets locally (system-font stack, hand-written CSS, vanilla JS) —
  no CDN, fonts, or external scripts.
- **Content-Security-Policy:** `default-src 'self'` (when
  `security.enable_csp` is true) prevents the page from loading or contacting
  anything external — enforces the offline guarantee in the browser.
- **Filename sanitization:** original filename sanitized before being echoed in
  `Content-Disposition`.
- **Size cap:** requests above `max_file_size_mb` rejected with `413`.
- **Memory note:** a single 500 MB job may transiently use ~1–1.5 GB RAM
  (input + working copy + output). Acceptable for local single-user use;
  documented in the README.

## Frontend / UX

Single page, iLovePDF-inspired, three visual states on one screen:

1. **Idle:** centered card, drag-and-drop zone ("Drop your PDF here or click to
   browse"), password field, "Unlock PDF" button. Selected filename shown once
   chosen.
2. **Working:** spinner + "Unlocking…" while the request is in flight.
3. **Result:**
   - Success → "✓ Your PDF is ready" with a large **Download** button (uses the
     blob URL) and an "Unlock another" reset link.
   - Error → friendly inline message (wrong password, invalid PDF, too large)
     with the form still usable for retry.

Styling: clean modern card UI, soft shadows, accent color, responsive — all from
local CSS. No build step, no JS framework, no external resources.

## Error Handling Summary

| Situation | Core | HTTP | User-facing message |
|---|---|---|---|
| Correct password | returns bytes | 200 | (download) |
| Wrong password | `WrongPassword` | 401 | "Incorrect password — please try again." |
| Not encrypted (passthrough on) | returns input | 200 | (download; optional notice) |
| Invalid/corrupt PDF | `InvalidPDF` | 400 | "This doesn't look like a valid PDF." |
| Non-PDF extension / no file | — | 400 | "Please choose a PDF file." |
| Too large | — | 413 | "File exceeds the 500 MB limit." |

## Testing Strategy

- **Core (`test_decryptor.py`):** build small encrypted PDFs at test time with
  pikepdf, then assert: correct password decrypts and result opens without a
  password; wrong password raises `WrongPassword`; unencrypted input handled per
  flag; garbage bytes raise `InvalidPDF`.
- **Routes (`test_app.py`):** Flask test client — happy path returns
  `application/pdf` with a download disposition; wrong password returns `401`
  JSON; missing/non-PDF file returns `400`; oversize returns `413`.
- **Offline check:** dependencies asserted to require no network; no external
  URLs present in frontend assets.

## Open Questions

None outstanding. Design approved by user on 2026-06-27.
