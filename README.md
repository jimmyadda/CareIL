# CareIL

Project decisions, implementation history, deployment notes, and future-work context are maintained in [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md). Read it before continuing development.

A mobile-first Flask application for a single-therapist clinic. It manages clients, appointments, session notes, files, messages, online appointment requests, and Word summaries.

## What changed in this version

- Modern calm clinic design with responsive tables, forms, dialogs, and navigation.
- Installable Progressive Web App (PWA) for phone and tablet use.
- Single-therapist workflow: the therapist is created automatically and appointments no longer require staff selection.
- Therapist profile replaces add/delete doctor management.
- Configurable booking days, opening hours, and session duration.
- Client bookings are restricted to availability and existing appointments.
- Word summary export from the client record.
- Secrets moved to environment variables; debug mode is disabled by default.
- Minimal dependency list and sensitive runtime data excluded from source control.

## Setup

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Run `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and provide strong values. Your process manager or shell must load these environment variables.
5. Run `python server.py`.
6. Open `http://127.0.0.1:5000`.

For production, place the app behind HTTPS and a production WSGI server. Do not run with `FLASK_DEBUG=true`.

## Mobile use

The interface is responsive and can be installed from Safari/Chrome using “Add to Home Screen.” This gives an app-like icon and standalone window without maintaining separate iOS and Android codebases.

## Security notes

Do not commit `.env`, `config.json`, SQLite databases, client uploads, logs, or real client data. If an email password was ever committed, revoke it and issue a new app password; removing it from a later commit is not enough to invalidate the exposed credential.

Before public production use, add CSRF protection, rate limiting, encrypted backups, audit logging, expiring portal links, and a formal privacy/security review appropriate to your jurisdiction.

## Google Calendar synchronization

1. In Google Cloud, enable the Google Calendar API.
2. Create an OAuth 2.0 Web application.
3. Add `http://127.0.0.1:5000/google-calendar/callback` as an authorized redirect URI for local use.
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in the environment.
5. Install `requirements.txt`, restart Flask, and open **Clinic settings → Google Calendar**.

Confirmed appointments are created in the connected primary calendar. Updates and deletions are synchronized too. Client-requested appointments are not synchronized until the therapist approves them. Refresh tokens are encrypted with `THERAPY_SECRET_KEY`; changing that key requires reconnecting Google Calendar.

Google Calendar and appointment-email end times use the session duration saved under **Clinic settings → Booking availability**. It is not duplicated in `.env`.
