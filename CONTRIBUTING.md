# Contributing

## Local setup

Create a virtual environment, install `requirements.txt`, copy `.env.example` to
`.env`, then run `python app.py`. Start the web client from `frontend` with
`npm install` and `npm run dev`.

## Quality checks

Run `pytest`, then `npm run build` in `frontend`. Keep scanner changes
defensive: never execute uploaded files or fetch attacker-controlled URLs.

## Pull requests

Keep changes focused, add or update tests, and describe security implications.
Do not commit API keys, `.env`, scan artifacts, or personal data.
