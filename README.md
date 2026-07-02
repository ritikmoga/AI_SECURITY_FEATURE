# AI Security Feature / ScamShield AI

A defensive Flask API for scanning URLs, messages, files, and decoded QR text for scam, phishing, and malware indicators.

This project was upgraded from a basic Flask app into a security scanning backend with safe heuristics, JSON reports, risk scoring, rate limiting, and optional external reputation-service clients.

## Features

- `POST /api/scan/url` - scans a URL with local phishing/scam heuristics
- `POST /api/scan/message` - scans message text, attachments metadata, and embedded URLs
- `POST /api/scan/file` - safely inspects uploaded files without executing them
- `POST /api/scan/qr` - scans decoded QR text or QR URLs
- `GET /api/scan/report/<scan_id>` - returns a saved JSON scan report
- `GET /api/health` - service health/status

## Risk Levels

| Score | Level |
|---:|---|
| 0-20 | Safe |
| 21-50 | Suspicious |
| 51-75 | High Risk |
| 76-100 | Dangerous |

## Safety Design

- Uploaded files are not executed.
- Files are stored only temporarily during scanning, then deleted.
- API keys are read from environment variables only.
- Local/private network URL fetching is avoided to reduce SSRF risk.
- External API checks are disabled by default.
- No real malicious samples are included in tests.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open:

```text
http://localhost:5000/api/health
```

## Example API Calls

### Scan URL

```bash
curl -X POST http://localhost:5000/api/scan/url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/login?next=https%3A%2F%2Fexample.org"}'
```

### Scan Message

```bash
curl -X POST http://localhost:5000/api/scan/message \
  -H "Content-Type: application/json" \
  -d '{"subject":"Check this", "body":"Visit https://example.com", "attachments":[{"filename":"invoice.pdf.exe"}]}'
```

### Scan File

```bash
curl -X POST http://localhost:5000/api/scan/file \
  -F "file=@sample.pdf"
```

### Scan Decoded QR Text

```bash
curl -X POST http://localhost:5000/api/scan/qr \
  -H "Content-Type: application/json" \
  -d '{"text":"https://example.com"}'
```

## Environment Variables

Create `.env` from `.env.example`:

```env
FLASK_DEBUG=false
PORT=5000
CORS_ORIGINS=*
MAX_FILE_SIZE_MB=10
RATE_LIMIT_PER_MINUTE=60
REPORT_STORAGE_PATH=./data/reports.json
EXTERNAL_CHECKS_ENABLED=false
GOOGLE_SAFE_BROWSING_API_KEY=
VIRUSTOTAL_API_KEY=
URLSCAN_API_KEY=
```

## Optional External Checks

Set this only after adding API keys:

```env
EXTERNAL_CHECKS_ENABLED=true
```

The current implementation supports optional lookup clients for:

- Google Safe Browsing
- VirusTotal
- urlscan.io lookup/search

## Run Tests

```bash
pytest -q
```

## Recommended GitHub Workflow

```bash
git checkout -b scanner-api-upgrade
# copy these upgraded files into your repo
git add .
git commit -m "Convert Flask app into defensive AI security scanner API"
git push -u origin scanner-api-upgrade
```

Then open a pull request into `main`.

## Production Next Steps

- Add authentication for private scan history.
- Move reports to PostgreSQL or MongoDB.
- Replace the in-memory rate limiter with Redis.
- Add frontend pages for URL, file, QR, and message scanning.
- Add queue workers for heavy file scans.
- Add ClamAV/YARA in an isolated worker container.
- Add CI/CD with tests and secret scanning.
