# CareIL Project Context

## v35 email verification enforcement

- Therapist accounts are created with `email_verified = 0`.
- Registration does not sign the therapist in before email verification.
- `/enter_email` keeps the user on the registration verification-code form.
- `/login` redirects unverified accounts to the email verification flow.
- `/verify` marks the account verified, consumes the one-time code, and signs the therapist in.
- Existing databases are migrated automatically by adding the `email_verified` column with a default value of `0`.
- Verification codes expire after five minutes and are deleted after successful use.
- `tests/test_registration_flow.py` covers early-login prevention, unverified-login blocking, code-form rendering, and activation after a valid code.

## v36 public SaaS foundation

- Logged-out `/` is a public SEO landing page; authenticated users still see the existing dashboard.
- `robots.txt`, `sitemap.xml`, canonical metadata, Open Graph metadata and SoftwareApplication structured data are included.
- `/demo/start` creates an isolated seeded demo tenant; external email, uploads, Google authorization, portal invitations and account deletion are blocked.
- Demo databases expire automatically after two hours and the app caps concurrent demo databases.
- Settings includes a Danger Zone requiring the current password and the exact phrase `DELETE CAREIL`.
- Account deletion suspends the tenant immediately, emails an undo link, and retains the database for a 24-hour recovery period.
- Signing in during the recovery window also offers account restoration.
- After the recovery window, tenant database and tenant uploads are permanently removed by lifecycle cleanup.
- Existing tenant databases receive additive lifecycle columns automatically; existing account/client data is preserved.
- `tests/test_saas_features.py` covers the landing page, demo isolation/seeding, additive migration and expired-demo cleanup.

Last consolidated: 2026-08-23

This file is the project handoff and continuity record for future CareIL work. It summarizes the useful decisions and implementation history from earlier conversations. It is not a verbatim chat transcript and contains no credentials or client records.

## Product purpose

CareIL is a Flask application for a small, single-therapist emotional-therapy clinic. Its primary workflows are:

- Therapist dashboard and account/profile management.
- Client records, intake details, uploaded documents, and session summaries.
- Appointment creation, schedule/calendar views, availability rules, and online requests.
- Secure client portal links sent by email.
- Client dashboard for appointments, personal contact details, and therapist messages.
- Word-document summaries and therapy-oriented record keeping.
- Hebrew and English interface support.
- Mobile-first web/PWA use on iPhone and desktop.

The application is meant to feel like a calm therapy practice, not a hospital or medical system.

## Terminology

Use these terms consistently:

| Avoid | Use |
| --- | --- |
| Doctor | Therapist |
| Patient, where client-facing | Client |
| Medical note | Session summary or appointment summary |
| Medical records | Session records |

Some database and source identifiers still use legacy names such as `doctor`, `patient`, and `medicalnote`. Do not rename those mechanically without a planned schema/API migration.

## Core product decisions

### Single therapist

- One authenticated account represents one therapist.
- Do not restore an “Add doctor” workflow.
- `/therapist` is the therapist profile page.
- Therapist profile changes should update the account identity used in the greeting and appointment workflow.
- The dashboard greeting must use the logged-in therapist’s name, for example “Welcome, Karin Adda.”

### Client portal

- Reuse `templates/portal.html`.
- Portal access is via secure, expiring links rather than a shared password.
- Portal invitation storage is created/migrated in `package/database.py`.
- Therapist actions required from the client record:
  - Send portal link.
  - Copy portal link.
  - Revoke links.
- Portal links are hashed in storage and can be revoked.
- Portal message actions must authorize against the portal session and client ID.
- Clients should not see internal uploaded files or therapy/session notes.
- The portal may show appointments, contact data, therapist messages, and appointment-request controls.

### Scheduling and availability

- Availability is configured at `/admin/availability` and stored in the clinic `settings` table.
- The database setting `APPOINTMENT_DURATION` is the single source of truth for session duration.
- The same duration must be used by:
  - Internal schedule availability.
  - Portal appointment requests.
  - Google Calendar event end time.
  - Email `.ics` calendar attachment end time.
  - `/calendar` visual event duration.
- Existing appointments and unavailable hours must appear disabled/gray before selection.
- Disabled/booked states must refresh both when clicking a date and when navigating the picker with Previous/Next arrows.
- This applies to the portal, `/patientform`, and `/appointment` flows.
- Requested portal appointments remain pending until therapist approval.

### Google Calendar

- One-way synchronization is currently implemented from confirmed CareIL appointments to the therapist’s primary Google Calendar.
- Appointment creation/update/delete attempts to create/update/delete the mapped Google event.
- Pending client requests are not synchronized until approved.
- `/calendar` includes a manual **Sync Google Calendar** action.
- Google Calendar settings page: `/admin/google-calendar`.
- Google OAuth routes:
  - `/google-calendar/connect`
  - `/google-calendar/callback`
  - `/google-calendar/sync`
  - `/google-calendar/disconnect`
- Gmail SMTP credentials are only for sending email and cannot authorize Google Calendar.
- Calendar uses Google OAuth with offline access and an encrypted refresh token stored per therapist account.
- Do not store therapy notes in Google Calendar.
- Calendar event title defaults to the privacy-conscious “Therapy appointment.” Client name inclusion is optional through `GOOGLE_CALENDAR_INCLUDE_CLIENT_NAME`.

Required deployment variables:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://YOUR_PUBLIC_DOMAIN/google-calendar/callback
THERAPY_TIMEZONE=Asia/Jerusalem
THERAPY_SECRET_KEY=...
THERAPY_HTTPS=true
```

Do not add session duration to `.env`; it is managed in `/admin/availability`.

### Email

- Existing SMTP settings remain responsible for client email delivery.
- Appointment email containing date/details, secure portal link, and `.ics` attachment is sufficient for the initial product.
- SMS is not required for the initial release. Consider it later only for reminder/no-show needs, with consent and opt-out handling.
- The approved therapy logo is used in branded emails.

## Visual design system

### Brand

- Product name: CareIL (Care Israel / Care I Love).
- Approved logo concept: two feminine hands facing forward, holding soil with a young leaf/plant emerging.
- Style: black outline drawing, simple app-icon treatment, transparent background.
- Use in navbar/title, portal, favicon/PWA icon, and email branding.

### Color

Use one primary gradient throughout the application:

```css
linear-gradient(135deg, #a3b18a 0%, #588157 100%)
```

The navbar gradient is the canonical gradient. Do not reintroduce the previous bright yellow/olive gradient using `#B3C82A` or `#E1E66D`.

Use solid olive `#708238` only for smaller accents, selected states, icons, and compatible borders. Keep page backgrounds neutral and cards white.

The shared design is primarily in:

- `static/modern-clinic.css`
- `static/modern-clinic.js`
- `static/login.css`
- `templates/portal.html` for portal-specific layout

### Navigation and mobile layout

- Top navigation uses the same sage gradient on every page.
- Language selection uses GB and Israel flag buttons; the old language combo remains hidden only as the existing handling bridge.
- Flags, Settings, and Logout form one compact action group.
- English layout: logo left, action group right.
- Hebrew layout: logo right, action group left, with reversed action order.
- Flag buttons must stay tappable on iPhone and must not sit underneath the navbar header layer.
- Mobile bottom navigation contains Home, Clients, Schedule, and Settings.
- Pages need sufficient safe-area/bottom padding so the fixed bottom navigation never hides the last control.

### Responsive tables

- Desktop retains tabular presentation.
- Mobile tables become compact cards.
- Client mobile cards show only full name and actions, not every database field.
- Avoid horizontal-only reading as the primary mobile experience.

## Language behavior

- Supported languages: English (`EN`) and Hebrew (`HE`).
- Preserve the existing `Translate.json` and language-selection mechanism.
- Language switching must update:
  - Dashboard text.
  - Inner-page labels.
  - Input placeholders.
  - Direction and alignment.
- `static/js/Helpers.js` handles translation, placeholders, and body language-direction classes.
- Hebrew pages are RTL; English pages are LTR.
- New visible UI should add appropriate `Translate.json` keys instead of hard-coded bilingual branching where practical.

## Important fixes already made

- Dashboard redesigned for a modern therapy clinic.
- Olive/sage branding standardized throughout the app.
- Approved logo added to primary application surfaces.
- Old language combo hidden; flag controls added.
- Dashboard and placeholder translation extended.
- Mobile flag touch/overlap issue addressed.
- Hebrew/English navbar sides and action order addressed.
- Settings-page mobile bottom scrolling/safe area addressed.
- Mobile client tables shortened to full name and actions.
- Missing and oversized patient-page icons/button visibility addressed.
- Patient detail loading from `/patientform?id=...` addressed.
- Patient file-upload section restored internally.
- Portal intentionally hides client files.
- Portal “Mark as read” authorization flow changed to use portal session/client ownership.
- Secure portal-link generation, copying, sending, and revocation added.
- Appointment picker unavailable/booked-hour behavior refreshed on both click and navigation.
- `/appointment` add-appointment behavior repaired.
- Session-summary page terminology and RTL/LTR controls added.
- Legacy template database typo around `tamplate`/`template` addressed during template work.
- Therapist profile route and single-account therapist behavior added.
- Google Calendar connection, database migration, synchronization, and manual sync UI added.
- Session duration centralized in database availability settings.
- Service-worker/PWA assets and mobile bottom navigation added.

## Data and database notes

- Current storage is SQLite with per-client database files under the configured database path.
- `DatabaseManager.connect_to_db` performs compatible schema checks/migrations for portal invitations and Google Calendar mappings.
- Google Calendar adds:
  - `google_calendar_connections`
  - `appointment.google_event_id`
- Secure portal access adds `portal_invitations` and supporting indexes.
- Runtime databases and uploads contain sensitive clinic data and must never be committed or included in a public source archive.
- `.env`, SQLite databases, uploads, and logs are excluded from clean source packages.

## Railway deployment

- Production callback must use the exact public HTTPS Railway/custom domain:

```text
https://YOUR_PUBLIC_DOMAIN/google-calendar/callback
```

- Add the exact same URI to the Google OAuth Web Application’s authorized redirect URIs.
- Configure secrets in Railway **Service → Variables**, not in a committed `.env`.
- Use `THERAPY_HTTPS=true` in production.
- Railway’s filesystem is ephemeral unless a persistent Volume is mounted.
- Persist both the database path and uploaded-client-file path, or migrate storage before production.
- If the production domain changes, update both Google Cloud’s redirect URI and `GOOGLE_REDIRECT_URI`.

## Security and privacy constraints

- Never commit real SMTP passwords, Google secrets, `.env`, client databases, uploads, or logs.
- Keep Google client secrets server-side.
- Refresh tokens are encrypted using a key derived from `THERAPY_SECRET_KEY`; changing the key requires reconnecting Google Calendar.
- Do not expose internal client files or session summaries through the portal.
- Use HTTPS and secure cookies in production.
- Before public clinical use, complete CSRF protection, rate limiting, audit logging, encrypted backup/restore, and a jurisdiction-appropriate privacy/security review.
- Replace any secret that was previously committed or shared; deleting it from a later version does not revoke it.

## Current source and artifacts

- Current consolidated package at the time of this handoff: v38.
- Current clean full-source archive: `CareIL-full-source-v38.zip`.
- v38 adds a searchable server-rendered Hebrew landing page at `/he`, RTL presentation, translated SEO metadata and a visible language toggle. It also compacts mobile client action buttons and gives the profile action additional width.
- v39 keeps explicit Log in/Sign up actions visible in the mobile landing header in both languages.
- Earlier small unified-color update predates the CareIL rename.
- The working source folder is `TherapyManager` in the current workspace (legacy technical folder name).
- Fresh deployments use `CareIL.db`, `databases/CareIL_default_client.db`, and `databases/CareIL_<client_key>.db`; no legacy database migration is required.
- Railway transactional email uses Resend over HTTPS through `RESEND_API_KEY` and `CAREIL_FROM_EMAIL`; SMTP remains only as a local fallback.
- Email verification and user loading safely recover from missing or stale browser sessions instead of raising `KeyError` or `FileNotFoundError`.
- The project root contains `README.md`, `.env.example`, and this `PROJECT_CONTEXT.md`.

## Known follow-up work

### v37 legal/compliance baseline

- Added public bilingual legal pages: Privacy, Terms, DPA, Cookies, Accessibility, Cancellation/Refunds, Subprocessors, and Security/Retention.
- Registration requires explicit acceptance of the current Privacy, Terms, and DPA versions. Marketing is a separate optional choice.
- Existing therapist accounts are redirected once to `/legal/accept` when the legal version changes.
- `legal_acceptances` stores document type/version, timestamp, selected language, IP, and user-agent in the tenant database; `accounts.marketing_consent` stores the optional marketing choice.
- Public legal pages are linked from the landing page, login and clinic settings and included in the sitemap.
- Railway operator/contact variables are documented in `.env.example`. The configured legal operator identity and email routes must be completed before launch.
- The documents are operational drafts, not legal certification. Israeli legal, privacy, accessibility, and information-security review remains required before using CareIL for real health information or paid subscriptions.

Prioritize these before treating the app as production-ready:

1. Add a production WSGI start command and confirm Railway uses its assigned `PORT`.
2. Configure and test Railway persistent storage or migrate databases/uploads to managed services.
3. Exercise the complete Google OAuth flow against the final public domain.
4. Add CSRF protection to all state-changing form and API actions.
5. Add login/portal rate limiting and security audit logging.
6. Test backup and restore, including encrypted off-site backups.
7. Complete a route-by-route Hebrew translation audit, especially newer settings/Google Calendar pages.
8. Add automated tests for portal authorization, appointment conflicts, schema migrations, and Calendar synchronization failures.
9. Review legacy SQL string interpolation and convert remaining dynamic queries to parameters.
10. Decide whether to keep per-client SQLite databases or migrate to PostgreSQL before broader multi-clinic use.

## Working rules for future changes

- Inspect this file and `README.md` before starting a new CareIL task.
- Preserve the existing language mechanism and database compatibility unless a migration is explicitly planned.
- Maintain the single-therapist model.
- Reuse the one canonical sage gradient.
- Test desktop, iPhone-width LTR, and iPhone-width RTL layouts.
- Test appointment availability on date click and picker arrow navigation.
- Keep portal output strictly client-safe.
- After changes, validate Python syntax, JavaScript syntax, JSON files, database migration behavior, and ZIP integrity.
- Produce a small update ZIP when practical and a clean full-source ZIP for milestone releases.
