# CareIL

## Bilingual public landing page (v38)

The searchable public site is available in English at `/` and in Hebrew at `/he`. The language control switches between server-rendered pages with matching RTL/LTR layouts, translated metadata and localized legal links.

The mobile header keeps separate Log in/Sign up (`כניסה`/`הרשמה`) controls visible alongside the language toggle.

The product-preview section uses optimized screenshots captured from the seeded CareIL demo dashboard and mobile client view rather than decorative empty placeholders.

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

A mobile-first Flask application for a single-therapist clinic. It manages clients, appointments, session summaries, files, messages, questionnaires, diagnoses, and online appointment requests.

## What changed in this version

- Modern calm clinic design with responsive tables, forms, dialogs, and navigation.
- Installable Progressive Web App (PWA) for phone and tablet use.
- Single-therapist workflow: the therapist is created automatically and appointments no longer require staff selection.
- Therapist profile replaces add/delete doctor management.
- Configurable booking days, opening hours, and session duration.
- Client bookings are restricted to availability and existing appointments.
- Per-client Details, Docs, Questionnaires and Appointments workspace.
- Reusable questionnaire templates can be assigned and emailed through the secure patient portal; completed answers return to the patient record.
- Reusable diagnosis types and patient-specific diagnosis history are available under Details.
- Session summaries can be linked to completed appointments and dictated in Hebrew in supported browsers.
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

`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are CareIL-wide application credentials and belong in Railway service variables, not tenant databases or browser forms. Each therapist uses the Connect button to choose their own Google account; only that account's encrypted refresh token is stored in the therapist's separate tenant database. The Calendar Sync button opens Google's account chooser automatically when no account is connected and acts as a catch-up sync after connection.

Google Calendar and appointment-email end times use the session duration saved under **Clinic settings → Booking availability**. It is not duplicated in `.env`.

## Transactional email on Railway

Railway deployments send verification, appointment, portal-link, and welcome emails through Resend's HTTPS API. Configure `RESEND_API_KEY` and `CAREIL_FROM_EMAIL` as Railway service variables. Gmail SMTP remains available only as a local fallback when the Resend variables are absent.
## Controlled registration

Public users request access at `/request-access`. The CareIL owner reviews requests at
`/careil-admin/access-requests`. Configure the existing owner account in Railway:

```env
CAREIL_OWNER_USERID=your-existing-login-userid
CAREIL_OWNER_EMAIL=your-notification-email@example.com
```

Approval sends a private, single-use registration link valid for seven days. A clinic
database is created only when the approved person completes registration.
## Facebook Page publishing

CareIL includes an owner-only Meta OAuth connection and an approval-gated post queue.
The marketing agent can create drafts through the API, but publishing requires an
explicit approval confirmation that is stored with the post audit record.

Configure these Railway service variables:

```text
META_APP_ID=<Meta app ID>
META_APP_SECRET=<Meta app secret>
META_LOGIN_CONFIG_ID=<Facebook Login for Business configuration ID>
META_REDIRECT_URI=https://www.careil.net/meta/callback
META_GRAPH_API_VERSION=v24.0
META_PAGE_ID=<optional Page ID when the Meta account manages multiple Pages>
CAREIL_SOCIAL_AGENT_KEY=<long random API key>
```

Keep the existing `THERAPY_SECRET_KEY` stable. It is also used to encrypt the saved
Facebook Page access token. Add `https://www.careil.net/meta/callback` as an exact
valid OAuth redirect URI in the Meta app.

The Meta app requests only:

- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`

Agent requests use `Authorization: Bearer <CAREIL_SOCIAL_AGENT_KEY>`:

```http
POST /careil-api/social/drafts
Content-Type: application/json

{"message":"Approved CareIL post text","image_url":"https://www.careil.net/static/img/social/careil-launch-post.jpeg"}
```

After the owner explicitly approves the exact draft:

```http
POST /careil-api/social/drafts/42/approve-and-publish
Content-Type: application/json

{
  "approval_confirmation":"APPROVED",
  "approval_reference":"Chat approval message 48217"
}
```

The second call both records the approval reference and publishes. It rejects missing
or malformed approval confirmations. The same workflow is also available to the
CareIL owner in **Settings → CareIL Social Publishing**.
