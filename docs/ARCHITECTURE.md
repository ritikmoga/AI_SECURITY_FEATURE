# Architecture

```text
React + Vite client
        |
        | HTTPS / JSON or multipart upload
        v
Flask API -> validation -> scanner modules -> risk scorer -> report store
        |                                               |
        | Google ID token verification                  +-> JSON report archive
        v
SQLite user/report store (local) or PostgreSQL schema (production)
```

The scanner is intentionally non-executing. URL checks use local heuristics and
optional reputation providers; uploaded files are read as data and deleted after
analysis. The browser decodes QR images locally before sending decoded text.
