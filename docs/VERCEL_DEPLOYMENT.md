# Vercel deployment

ScamShield can be deployed as a public web app on Vercel. Vercel serves the
React build from its CDN and routes `/api/*` requests to the Flask Python
Function in `api/index.py`.

## Required production environment variables

Set these in **Vercel Project Settings → Environment Variables**:

```env
AUTH_SECRET_KEY=<a long random secret, at least 32 characters>
DATABASE_URL=<managed PostgreSQL connection string>
CORS_ORIGINS=https://your-project.vercel.app
GOOGLE_OAUTH_CLIENT_ID=<Google web OAuth client ID>
ADMIN_EMAILS=<comma-separated administrator emails>
```

Optional: `REDIS_URL`, Google Safe Browsing, VirusTotal, and urlscan.io keys.

## Deploy

1. Import `ritikmoga/AI_SECURITY_FEATURE` into Vercel.
2. Keep the repository root as the Vercel root directory.
3. Add the environment variables above and deploy.
4. In Google Cloud, add the final Vercel domain as an Authorized JavaScript
   origin before enabling Google Sign-In.

## Cloud limitations

Vercel functions are stateless and do not have access to visitors’ devices.

## Data storage

Without `DATABASE_URL`, the app uses SQLite in Vercel's temporary `/tmp`
directory so the function can start. This data can disappear whenever Vercel
creates a new function instance. For persistent user accounts and reports, set
`DATABASE_URL` to a hosted PostgreSQL connection string before public use.
Device-folder scans remain a local-only feature. For persistent report history,
configure PostgreSQL through `DATABASE_URL`; local JSON/SQLite storage is only
for development.
