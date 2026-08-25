# CareIL

## Bilingual public landing page (v38)

The searchable public site is available in English at `/` and in Hebrew at `/he`. The language control switches between server-rendered pages with matching RTL/LTR layouts, translated metadata and localized legal links.

On mobile, client-card actions use compact proportional widths so longer Hebrew labels remain readable.

## Legal and consent pages (v37)

CareIL includes public English and Hebrew pages for Privacy, Terms, Data Processing, Cookies, Accessibility, Cancellation/Refunds, Subprocessors, and Security/Retention. New registrations must accept the current Privacy Policy, Terms of Service, and DPA. Existing therapist accounts are prompted once after a legal-document version changes. The tenant database records the document type/version, time, language, IP address, and browser user agent; marketing consent remains separate and optional.

These pages are launch drafts, not legal certification. Before accepting real clinical data or payments, set the operator details below in Railway, make the email addresses operational, and obtain Israeli legal/privacy review:

```text
CAREIL_LEGAL_NAME=the operator's legal person/company name
CAREIL_LEGAL_ADDRESS=the operator's business/contact address
CAREIL_SUPPORT_EMAIL=support@careil.net
CAREIL_PRIVACY_EMAIL=privacy@careil.net
CAREIL_ACCESSIBILITY_EMAIL=accessibility@careil.net
```

No consent banner is shown because the current app describes only essential session/security cookies. Add a consent mechanism before adding non-essential analytics, advertising, or tracking technologies.

See [`LEGAL_LAUNCH_CHECKLIST.md`](LEGAL_LAUNCH_CHECKLIST.md) for the operator details, security, Google OAuth, client-consent, accessibility, and legal-review work that remains before a real-data or paid launch.

## Public site, demo and account recovery

- Logged-out visitors see the public product page at `/`; authenticated therapists continue to the dashboard.
- `/demo/start` creates a fictional, isolated demo workspace that expires automatically after two hours.
- Demo workspaces cannot send email, upload files, connect Google Calendar, send portal links or delete accounts.
- Settings → Danger Zone schedules complete workspace deletion after a 24-hour recovery period.
- Therapists can undo deletion from the emailed link or by signing in during the recovery period.
- Permanent cleanup removes the tenant database and its tenant upload directory; Railway Volume storage remains mounted for all other tenants.

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

Before public production use, add CSRF protection, rate limiting, encrypted backups, broader security audit logging, and a formal privacy/security review appropriate to your jurisdiction.

## Google Calendar synchronization

1. In Google Cloud, enable the Google Calendar API.
2. Create an OAuth 2.0 Web application.
3. Add `http://127.0.0.1:5000/google-calendar/callback` as an authorized redirect URI for local use.
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in the environment.
5. Install `requirements.txt`, restart Flask, and open **Clinic settings → Google Calendar**.

Confirmed appointments are created in the connected primary calendar. Updates and deletions are synchronized too. Client-requested appointments are not synchronized until the therapist approves them. Refresh tokens are encrypted with `THERAPY_SECRET_KEY`; changing that key requires reconnecting Google Calendar.

Google Calendar and appointment-email end times use the session duration saved under **Clinic settings → Booking availability**. It is not duplicated in `.env`.

## Transactional email on Railway

Railway deployments send verification, appointment, portal-link, and welcome emails through Resend's HTTPS API. Configure `RESEND_API_KEY` and `CAREIL_FROM_EMAIL` as Railway service variables. Gmail SMTP remains available only as a local fallback when the Resend variables are absent.
