# ScamShield AI Frontend

A fast React + Vite + TypeScript frontend for the ScamShield AI Flask backend.

## Features

- Futuristic defensive scanner dashboard
- API health status card
- URL scanner
- Message scanner
- File scanner with multipart upload
- QR scanner with client-side QR image decoding
- Report lookup by scan ID
- Local browser scan history
- Responsive desktop/mobile UI

## Required backend

Start the Flask backend first. If port `5000` is busy on macOS, run:

```bash
PORT=5001 python app.py
```

Confirm backend health:

```text
http://127.0.0.1:5001/api/health
```

## Run frontend locally

```bash
npm install
cp .env.example .env
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Environment

`.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:5001
```

Change this when the Flask backend is deployed.

## Project structure

```text
src/
  components/
    HealthCard.tsx
    Hero.tsx
    HistoryPanel.tsx
    ResultCard.tsx
    RiskBadge.tsx
    RiskGauge.tsx
    ScannerPanel.tsx
  lib/
    api.ts
    history.ts
    qr.ts
  App.tsx
  main.tsx
  styles.css
```

## Safety note

This UI is for defensive scanning only. It does not execute uploaded files. File analysis is performed by the backend through static checks.
