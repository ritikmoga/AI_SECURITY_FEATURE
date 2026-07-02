# API Reference

## GET /api/health

Returns API status and configuration limits.

## POST /api/scan/url

Request:

```json
{"url":"https://example.com"}
```

Response:

```json
{
  "status": "success",
  "data": {
    "scan_id": "uuid",
    "risk_score": 0,
    "risk_level": "Safe",
    "findings": []
  }
}
```

## POST /api/scan/message

Request:

```json
{
  "subject": "Message subject",
  "body": "Message body with optional URLs",
  "attachments": [{"filename":"invoice.pdf"}]
}
```

## POST /api/scan/file

Use multipart form field named `file`.

## POST /api/scan/qr

Request:

```json
{"text":"decoded QR text or URL"}
```

## GET /api/scan/report/<scan_id>

Returns a previously saved report.
