# Google Sign-In setup

Create a Google Cloud OAuth 2.0 Web Application client. Add each frontend URL to
**Authorized JavaScript origins**, then configure its client ID in both `.env`
and `frontend/.env`. The backend verifies the returned ID token against this
same audience before creating a session; do not trust user details supplied by
the browser alone.
