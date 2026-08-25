# CareIL legal and privacy launch checklist

This checklist accompanies the versioned in-app legal pages. It is an operational aid, not legal advice or certification.

## Before accepting real clinic information

- Obtain review by an Israeli lawyer familiar with privacy, health information, SaaS contracts and consumer law.
- Complete the legal operator name and contact address in Railway. Do not publish with `CareIL` as a placeholder if a person or registered company is the actual operator.
- Make `support@careil.net`, `privacy@careil.net`, and `accessibility@careil.net` working mailboxes or forwarding aliases and define who monitors them.
- Determine CareIL's obligations under the Israeli Privacy Protection Law and Data Security Regulations, including database registration/notification, security level, data mapping, incident response and service-provider agreements.
- Complete an accessibility assessment. The current statement intentionally does not claim certification or full compliance.
- Define subscription price, billing period, renewal, cancellation and refund rules before taking payment, then align the published Refund Policy and checkout disclosure.
- Execute appropriate contracts with Railway, Resend, Google and any future subprocessor; keep the public Subprocessors page current.
- Establish encrypted backup/restore, access review, breach-response, deletion verification and audit procedures.
- Add CSRF protection and rate limiting and complete an application security review.
- Give each therapist a suitable client/guardian privacy notice and clinical consent form. CareIL's Terms and DPA do not replace therapist-to-client consent.

## Google Calendar production release

- Keep OAuth client credentials server-side in Railway.
- Use `https://www.careil.net/google-calendar/callback` exactly in Google Cloud and `GOOGLE_REDIRECT_URI`.
- Publish `https://www.careil.net/legal/privacy` in the OAuth consent configuration.
- Request only the Calendar scope actually used by the product.
- Complete Google's required production verification before offering Calendar connection broadly.
- Re-consent users if CareIL materially changes how Google user data is accessed or used.

## Document-version workflow

1. Update both English and Hebrew content in `package/legal_documents.py`.
2. Change `LEGAL_VERSION` and the effective date.
3. Deploy. Existing therapist accounts will be prompted to accept the new version once.
4. Preserve acceptance records and a copy of each historical document version required for evidentiary purposes.
5. For a material privacy change, provide clear notice before the new processing begins.

## Official reference points

- Israeli Privacy Protection Authority: https://www.gov.il/he/departments/the_privacy_protection_authority
- Serious data-security incident reporting: https://www.gov.il/he/service/report-of-data-breach
- Israeli internet accessibility information: https://www.gov.il/he/service/application_for_exemption_internet_people_with_disabilities
- Consumer Protection and Fair Trade Authority: https://www.gov.il/en/departments/consumer_protection_and_fair_trade_authority
- Google API Services User Data Policy: https://developers.google.com/terms/api-services-user-data-policy

