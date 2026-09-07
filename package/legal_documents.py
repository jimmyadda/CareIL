"""Versioned bilingual legal-document content for CareIL."""

LEGAL_VERSION = "2026-08-25-v1"
LEGAL_EFFECTIVE_DATE = "25 August 2026"


def _doc(title, intro, sections):
    return {"title": title, "intro": intro, "sections": sections}


DOCUMENTS = {
    "privacy": {
        "en": _doc(
            "Privacy Policy",
            "This policy explains how CareIL processes information when therapists use the service and when visitors use the public website.",
            [
                ("1. Roles and scope", [
                    "For account, security, billing and website administration information, CareIL acts as the party responsible for determining the purposes of processing.",
                    "For client records entered by a therapist, the therapist or clinic controls the information and CareIL processes it only to provide the service. Therapists are responsible for a lawful basis, clinical confidentiality and notices or consents required from clients and guardians.",
                    "CareIL is intended for professional therapists. It is not directed to children for independent registration."
                ]),
                ("2. Information we process", [
                    "Account information may include name, email, phone, clinic details, language, authentication records, legal-document acceptances and support communications.",
                    "Clinic information may include client identity and contact information, appointments, availability, session summaries, messages, uploaded files and portal invitations. This may constitute health information or information of special sensitivity.",
                    "Technical information may include IP address, browser and device information, request logs, security events and essential session-cookie data. Google Calendar information is processed only when a therapist chooses to connect Google."
                ]),
                ("3. Purposes and legal grounds", [
                    "We process information to provide and secure CareIL, authenticate users, synchronize requested integrations, deliver transactional messages, support users, maintain audit records, comply with law and improve reliability.",
                    "We do not sell client records or use therapy content for advertising. Marketing messages require a separate optional choice and can be stopped at any time."
                ]),
                ("4. Google user data", [
                    "CareIL requests permission to create, update and delete events managed by CareIL in the connected Google Calendar. Access is limited to the functionality requested by the therapist.",
                    "Google refresh tokens are encrypted and stored in the therapist's tenant database. CareIL does not use Google user data for advertising, credit decisions or unrelated analytics, and does not transfer it except as necessary to provide or secure the requested integration, comply with law, or with the user's explicit direction.",
                    "CareIL's use of information received from Google APIs is subject to the Google API Services User Data Policy, including Limited Use requirements."
                ]),
                ("5. Service providers and transfers", [
                    "CareIL may use Railway for application hosting and storage, Resend for transactional email, and Google for optional Calendar integration. The current list appears on the Subprocessors page.",
                    "Providers may process information outside Israel. CareIL uses contractual and technical measures intended to protect transferred information as required by applicable law."
                ]),
                ("6. Security and retention", [
                    "CareIL uses HTTPS, password hashing, tenant-separated databases, access controls, encrypted Google refresh tokens and expiring portal invitations. No system can guarantee absolute security.",
                    "Information is retained while the account is active and as necessary for security, dispute resolution and legal obligations. Account deletion suspends the workspace immediately and allows restoration for 24 hours. After the recovery period, active tenant data and tenant uploads are scheduled for permanent removal. Limited provider or security records may remain only for legitimate legal, fraud-prevention or technical retention periods."
                ]),
                ("7. Rights and choices", [
                    "Users may request access, correction, export or deletion of their account information and may disconnect Google Calendar. Client requests concerning clinical records should normally be directed to the responsible therapist, who may ask CareIL for assistance.",
                    "Privacy requests can be sent to the privacy contact shown below. Identity verification may be required. Rights may be limited where retention is required by law or necessary to protect others."
                ]),
                ("8. Changes and contact", [
                    "Material changes will be identified by a new policy version and, where required, users will be asked to accept them. Mandatory rights under applicable law are not limited by this policy."
                ]),
            ],
        ),
        "he": _doc(
            "מדיניות פרטיות",
            "מדיניות זו מסבירה כיצד CareIL מעבדת מידע כאשר מטפלים משתמשים בשירות וכאשר מבקרים משתמשים באתר הציבורי.",
            [
                ("1. תפקידים ותחולה", [
                    "ביחס למידע על חשבון, אבטחה, חיוב וניהול האתר, CareIL היא הגורם הקובע את מטרות העיבוד.",
                    "ביחס לרשומות לקוחות שמזין מטפל, המטפל או הקליניקה הם בעלי השליטה במידע ו-CareIL מעבדת אותו רק לצורך אספקת השירות. המטפל אחראי לבסיס חוקי, לסודיות מקצועית ולמסירת הודעות או קבלת הסכמות מלקוחות ומאפוטרופוסים.",
                    "CareIL מיועדת למטפלים מקצועיים ואינה מיועדת לרישום עצמאי של ילדים."
                ]),
                ("2. המידע שאנו מעבדים", [
                    "מידע החשבון עשוי לכלול שם, דוא״ל, טלפון, פרטי קליניקה, שפה, רישומי אימות, אישור מסמכים משפטיים ופניות לתמיכה.",
                    "מידע הקליניקה עשוי לכלול פרטי זיהוי וקשר של לקוחות, פגישות, זמינות, סיכומי טיפול, הודעות, קבצים וקישורים לפורטל. מידע זה עשוי להיות מידע רפואי או מידע בעל רגישות מיוחדת.",
                    "מידע טכני עשוי לכלול כתובת IP, דפדפן ומכשיר, יומני בקשות, אירועי אבטחה ומידע של עוגיית התחברות חיונית. מידע Google Calendar מעובד רק אם המטפל בוחר להתחבר."
                ]),
                ("3. מטרות ובסיסי העיבוד", [
                    "המידע משמש לאספקת CareIL ואבטחתה, אימות משתמשים, הפעלת שילובים מבוקשים, משלוח הודעות שירות, תמיכה, ניהול רישומי ביקורת, קיום הוראות דין ושיפור אמינות השירות.",
                    "איננו מוכרים רשומות לקוחות ואיננו משתמשים בתוכן טיפולי לפרסום. דיוור שיווקי מחייב בחירה נפרדת ואופציונלית."
                ]),
                ("4. מידע משתמשי Google", [
                    "CareIL מבקשת הרשאה ליצור, לעדכן ולמחוק אירועים שמנוהלים על-ידי CareIL ביומן Google המחובר. הגישה מוגבלת לפונקציונליות שביקש המטפל.",
                    "אסימוני הרענון של Google מוצפנים ונשמרים במסד הנתונים הנפרד של המטפל. המידע אינו משמש לפרסום, החלטות אשראי או ניתוח שאינו קשור לשירות, ואינו מועבר אלא לצורך אספקת השילוב, אבטחתו, קיום דין או לפי הוראה מפורשת של המשתמש.",
                    "השימוש במידע שמתקבל מ-Google APIs כפוף למדיניות נתוני המשתמש של Google ולדרישות Limited Use."
                ]),
                ("5. ספקים והעברות מידע", [
                    "CareIL עשויה להשתמש ב-Railway לאירוח ואחסון, ב-Resend לדוא״ל תפעולי וב-Google לשילוב יומן אופציונלי. הרשימה המעודכנת מופיעה בעמוד ספקי המשנה.",
                    "הספקים עשויים לעבד מידע מחוץ לישראל. CareIL משתמשת באמצעים חוזיים וטכנולוגיים שנועדו להגן על מידע מועבר בהתאם לדין החל."
                ]),
                ("6. אבטחה ושמירה", [
                    "CareIL משתמשת ב-HTTPS, גיבוב סיסמאות, מסדי נתונים נפרדים בין מטפלים, בקרות גישה, הצפנת אסימוני Google וקישורי פורטל שפג תוקפם. אין מערכת היכולה להבטיח אבטחה מוחלטת.",
                    "המידע נשמר כל עוד החשבון פעיל ולפי הצורך לצורכי אבטחה, בירור מחלוקות וחובות חוקיות. בקשת מחיקה משעה את סביבת העבודה ומאפשרת שחזור במשך 24 שעות. לאחר מכן הנתונים הפעילים והקבצים מתוזמנים למחיקה קבועה. רישומים מוגבלים עשויים להישמר רק לתקופות הנדרשות מטעמים חוקיים, מניעת הונאה או צורך טכני."
                ]),
                ("7. זכויות ובחירות", [
                    "משתמשים רשאים לבקש גישה, תיקון, ייצוא או מחיקה של מידע החשבון ולנתק את Google Calendar. בקשות של לקוחות לגבי רשומה טיפולית יש להפנות בדרך כלל למטפל האחראי, שיכול לבקש את סיוע CareIL.",
                    "ניתן לפנות לכתובת הפרטיות המופיעה להלן. ייתכן שנבקש אימות זהות. זכויות עשויות להיות מוגבלות כאשר קיימת חובת שמירה בדין או צורך להגן על אחרים."
                ]),
                ("8. שינויים ויצירת קשר", [
                    "שינויים מהותיים יסומנו בגרסה חדשה ובמקום שנדרש נבקש אישור מחדש. אין במדיניות זו כדי לגרוע מזכויות קוגנטיות לפי דין."
                ]),
            ],
        ),
    },
    "terms": {
        "en": _doc("Terms of Service", "These Terms govern professional use of the CareIL web service.", [
            ("1. Eligibility and accounts", ["Users must be at least 18 and authorized to operate the relevant clinic. Account details must be accurate and credentials must be protected. Each account is personal unless CareIL expressly enables organizational access."]),
            ("2. Service role", ["CareIL is administrative software, not a healthcare provider, emergency service, clinical supervisor, diagnosis tool or substitute for professional judgment. Therapists remain solely responsible for clinical services, record content, consent, retention duties and communications with clients."]),
            ("3. Permitted use", ["CareIL may be used only for lawful professional purposes. Users must not access another tenant, upload unlawful or malicious content, test security without permission, misuse portal links, resell access without authorization or use the service to harm or discriminate."]),
            ("4. Sensitive information", ["Users must collect and enter only information reasonably necessary for care and administration, obtain required notices and consents, restrict access, and avoid placing therapy notes or client names in third-party calendars unless lawful and intentionally enabled."]),
            ("5. Availability and changes", ["CareIL may maintain, change or discontinue features and may suspend access to protect users or the service. No uninterrupted or error-free service is promised. Users should maintain appropriate continuity and export procedures for their professional obligations."]),
            ("6. Fees and cancellation", ["Fees, billing periods and included features are those shown at purchase. Subscriptions may renew until cancelled. Mandatory cancellation and refund rights under applicable consumer law remain unaffected. Additional details appear in the Cancellation and Refund Policy."]),
            ("7. Intellectual property", ["CareIL and its software, design and branding remain the operator's property. Users retain rights in their clinic content and grant CareIL only the limited rights necessary to host, process, secure and transmit it to provide the service."]),
            ("8. Liability", ["To the extent permitted by law, CareIL is not liable for clinical decisions, missed appointments, user-entered errors, third-party services or indirect losses. Nothing excludes liability or rights that cannot legally be excluded. Users remain responsible for professional insurance and compliance."]),
            ("9. Termination", ["A user may request deletion through the Danger Zone. CareIL may suspend or terminate accounts for serious breach, unlawful activity, security risk or non-payment, subject to applicable law and reasonable data-return arrangements."]),
            ("10. Law and contact", ["These Terms are governed by the laws of the State of Israel, without limiting mandatory protections that apply to a user. Disputes are subject to the competent courts in Israel unless mandatory law provides otherwise."]),
        ]),
        "he": _doc("תנאי שימוש", "תנאים אלה מסדירים את השימוש המקצועי בשירות האינטרנט CareIL.", [
            ("1. כשירות וחשבונות", ["המשתמש חייב להיות בן 18 לפחות ומורשה להפעיל את הקליניקה הרלוונטית. יש למסור פרטים נכונים ולשמור על סודיות אמצעי ההתחברות. החשבון אישי אלא אם CareIL אפשרה במפורש גישה ארגונית."]),
            ("2. תפקיד השירות", ["CareIL היא תוכנה מנהלית ואינה ספק שירותי בריאות, שירות חירום, הדרכה קלינית, כלי אבחון או תחליף לשיקול דעת מקצועי. המטפל אחראי לשירות הקליני, לתוכן הרשומות, להסכמות, לחובות שמירה ולקשר עם הלקוחות."]),
            ("3. שימוש מותר", ["מותר להשתמש בשירות רק למטרות מקצועיות וחוקיות. אין לגשת לסביבה של מטפל אחר, להעלות תוכן בלתי חוקי או זדוני, לבדוק אבטחה ללא רשות, לעשות שימוש לרעה בקישורי פורטל, למכור גישה ללא אישור או להשתמש בשירות לפגיעה או אפליה."]),
            ("4. מידע רגיש", ["יש לאסוף ולהזין רק מידע שנדרש באופן סביר לטיפול ולניהול, למסור הודעות ולקבל הסכמות כנדרש, להגביל גישה ולהימנע מהצגת שמות או תוכן טיפולי ביומנים חיצוניים אלא אם הדבר חוקי והופעל במכוון."]),
            ("5. זמינות ושינויים", ["CareIL רשאית לתחזק, לשנות או להפסיק תכונות ולהשעות גישה לצורך הגנת משתמשים או השירות. השירות אינו מובטח כרציף או נטול שגיאות. על המטפל לקיים נהלי המשכיות וייצוא מתאימים לחובותיו המקצועיות."]),
            ("6. תשלום וביטול", ["המחיר, תקופת החיוב והתכונות הם כפי שהוצגו בעת הרכישה. מנוי עשוי להתחדש עד לביטולו. זכויות ביטול והחזר קוגנטיות לפי דין נשמרות. פרטים נוספים במדיניות הביטול וההחזרים."]),
            ("7. קניין רוחני", ["התוכנה, העיצוב והמותג CareIL שייכים למפעיל. המשתמש שומר על זכויותיו בתוכן הקליניקה ומעניק ל-CareIL רק הרשאה מוגבלת הדרושה לאחסון, עיבוד, אבטחה והעברה לצורך אספקת השירות."]),
            ("8. אחריות", ["בכפוף לדין, CareIL אינה אחראית להחלטות קליניות, פגישות שהוחמצו, שגיאות שהזין משתמש, שירותי צד שלישי או נזקים עקיפים. אין בכך כדי לשלול אחריות או זכויות שלא ניתן לשלול בדין. המטפל אחראי לביטוח מקצועי ולעמידה בדין."]),
            ("9. סיום", ["ניתן לבקש מחיקה באזור הסכנה. CareIL רשאית להשעות או לסיים חשבון בשל הפרה מהותית, פעילות בלתי חוקית, סיכון אבטחה או אי-תשלום, בכפוף לדין ולהסדר סביר להחזרת מידע."]),
            ("10. דין ויצירת קשר", ["על התנאים חל דין מדינת ישראל, מבלי לגרוע מהגנות קוגנטיות החלות על המשתמש. סמכות השיפוט נתונה לבתי המשפט המוסמכים בישראל אלא אם דין מחייב קובע אחרת."]),
        ]),
    },
    "dpa": {
        "en": _doc("Data Processing Agreement", "This DPA forms part of the CareIL Terms when a therapist enters client information into CareIL.", [
            ("1. Parties and roles", ["The therapist or clinic is the controller (or equivalent responsible party) for client information. The CareIL operator is the processor/service provider and processes that information only on documented instructions represented by use of the service and these terms."]),
            ("2. Processing details", ["Subject matter: hosting and operating clinic-management functions. Duration: the account term plus permitted retention. Data subjects: clients, guardians, family contacts and clinic personnel. Data types may include identity, contact, appointments, communications, files and therapy or health-related records."]),
            ("3. CareIL obligations", ["CareIL will process client information only to provide, secure and support the service or as required by law; require confidentiality; apply appropriate technical and organizational safeguards; assist reasonably with rights requests, security incidents and deletion; and notify the controller without undue delay after confirming a reportable breach affecting its data."]),
            ("4. Therapist obligations", ["The therapist determines lawful purposes and instructions, provides required privacy information, obtains necessary consent, uses appropriate account security, limits data to what is needed, responds to clients, and ensures professional and statutory retention requirements are met."]),
            ("5. Subprocessors", ["The therapist authorizes the subprocessors listed on CareIL's Subprocessors page. CareIL will impose data-protection duties appropriate to their services and will publish material changes. A therapist with a legally grounded objection should contact CareIL before the change takes effect."]),
            ("6. International transfers", ["Where information is processed outside its country of origin, the parties will rely on an available legal transfer mechanism and supplementary safeguards where required. The therapist authorizes transfers necessary for the listed hosting, email and optional Google integration services."]),
            ("7. Security and incidents", ["Measures include transport encryption, password hashing, tenant separation, access controls, encrypted Google tokens, expiring portal invitations, logging and controlled deletion. Each party will cooperate on incident assessment and legally required notifications according to its role."]),
            ("8. Return, deletion and audit", ["During an active account, the therapist may access and export information through available features. On verified deletion, CareIL removes active tenant data after the recovery period, subject to narrowly limited legal or provider retention. CareIL will provide reasonable compliance information; intrusive audits require advance agreement, confidentiality and proportionality."]),
        ]),
        "he": _doc("נספח עיבוד מידע (DPA)", "נספח זה הוא חלק מתנאי CareIL כאשר מטפל מזין מידע לקוחות למערכת.", [
            ("1. הצדדים והתפקידים", ["המטפל או הקליניקה הם בעלי השליטה במידע הלקוחות. מפעיל CareIL הוא מחזיק/מעבד מידע ומעבד אותו רק לפי הוראות מתועדות המשתקפות בשימוש בשירות ובתנאים אלה."]),
            ("2. פרטי העיבוד", ["נושא: אירוח והפעלת כלי ניהול קליניקה. משך: תקופת החשבון ותקופות שמירה מותרות. נושאי מידע: לקוחות, אפוטרופוסים, אנשי קשר וצוות הקליניקה. סוגי מידע: זיהוי, קשר, פגישות, תקשורת, קבצים ומידע טיפולי או רפואי."]),
            ("3. התחייבויות CareIL", ["CareIL תעבד מידע רק לאספקה, אבטחה ותמיכה בשירות או לפי דין; תחיל חובת סודיות; תפעיל אמצעים טכנולוגיים וארגוניים מתאימים; תסייע באופן סביר בבקשות זכויות, אירועי אבטחה ומחיקה; ותודיע לבעל השליטה ללא דיחוי בלתי סביר לאחר אימות אירוע המחייב דיווח ונוגע למידע שלו."]),
            ("4. התחייבויות המטפל", ["המטפל קובע מטרות והוראות חוקיות, מוסר הודעות פרטיות, מקבל הסכמות נדרשות, מאבטח את החשבון, מצמצם מידע לנדרש, מטפל בפניות לקוחות ומקיים חובות שמירה מקצועיות וחוקיות."]),
            ("5. ספקי משנה", ["המטפל מאשר את ספקי המשנה המפורטים בעמוד ספקי המשנה. CareIL תחיל עליהם חובות הגנה המתאימות לשירות ותפרסם שינויים מהותיים. התנגדות מבוססת דין יש להעביר לפני כניסת השינוי לתוקף."]),
            ("6. העברות בינלאומיות", ["כאשר מידע מעובד מחוץ למדינת המקור, הצדדים יסתמכו על מנגנון העברה חוקי זמין ועל הגנות משלימות לפי הצורך. המטפל מאשר העברות הדרושות לאירוח, דוא״ל ושילוב Google האופציונלי."]),
            ("7. אבטחה ואירועים", ["האמצעים כוללים הצפנה בתעבורה, גיבוב סיסמאות, הפרדת סביבות מטפלים, בקרות גישה, הצפנת אסימוני Google, קישורי פורטל זמניים, רישום אירועים ומחיקה מבוקרת. הצדדים ישתפו פעולה בבדיקת אירועים ובדיווחים הנדרשים לפי תפקידם."]),
            ("8. החזרה, מחיקה וביקורת", ["בחשבון פעיל המטפל יכול לגשת ולייצא מידע באמצעות התכונות הזמינות. לאחר בקשת מחיקה מאומתת, CareIL מסירה מידע פעיל בתום חלון השחזור, בכפוף לשמירה משפטית או טכנית מוגבלת. CareIL תמסור מידע תאימות סביר; ביקורת פולשנית דורשת תיאום, סודיות ומידתיות."]),
        ]),
    },
    "cookies": {
        "en": _doc("Cookie Policy", "CareIL currently uses essential browser storage needed to operate and secure the service.", [
            ("Essential cookies", ["The login session cookie remembers authentication, tenant context, language and security state. It is necessary for the service and cannot be disabled through CareIL without making authenticated features unavailable."]),
            ("Analytics and advertising", ["CareIL does not currently place third-party advertising cookies or optional analytics cookies. If optional analytics or marketing technologies are introduced, this policy and the consent controls will be updated before they are activated where consent is required."]),
            ("Browser controls", ["Users may remove cookies through browser settings. Removing the CareIL session cookie logs the user out and may interrupt verification or integration flows."]),
        ]),
        "he": _doc("מדיניות עוגיות", "CareIL משתמשת כיום באחסון דפדפן חיוני הנדרש להפעלה ולאבטחת השירות.", [
            ("עוגיות חיוניות", ["עוגיית ההתחברות זוכרת אימות, סביבת מטפל, שפה ומצב אבטחה. היא חיונית ולא ניתן להשביתה דרך CareIL בלי לפגוע בתכונות המחייבות התחברות."]),
            ("ניתוח ופרסום", ["CareIL אינה מפעילה כיום עוגיות פרסום של צד שלישי או עוגיות ניתוח אופציונליות. אם יתווספו טכנולוגיות כאלה, המדיניות וכלי ההסכמה יעודכנו מראש במקום שבו נדרשת הסכמה."]),
            ("בקרות דפדפן", ["ניתן להסיר עוגיות בהגדרות הדפדפן. הסרת עוגיית CareIL מנתקת את המשתמש ועלולה להפסיק תהליכי אימות או שילוב."]),
        ]),
    },
    "accessibility": {
        "en": _doc("Accessibility Statement", "CareIL aims to provide an accessible service and is being improved toward WCAG and Israeli Standard 5568 level AA practices.", [
            ("Measures", ["The service uses semantic headings, labelled controls, keyboard-operable navigation, responsive layouts, visible focus behavior, text alternatives and support for browser zoom where implemented."]),
            ("Known limitations", ["Some legacy administrative screens and third-party components may not yet fully meet the target. CareIL does not claim completed certification or a formal accessibility audit at this stage."]),
            ("Assistance and feedback", ["If a user encounters an accessibility barrier, contact the accessibility address below with the page, device and problem. CareIL will make reasonable efforts to provide an accessible alternative and correct the issue."]),
        ]),
        "he": _doc("הצהרת נגישות", "CareIL שואפת לספק שירות נגיש ופועלת לשיפור המערכת בהתאם לעקרונות WCAG ותקן ישראלי 5568 ברמה AA.", [
            ("התאמות", ["השירות משתמש בכותרות סמנטיות, פקדים מתויגים, ניווט מקלדת, פריסות רספונסיביות, סימון מיקוד, חלופות טקסט ותמיכה בהגדלת דפדפן במקומות שבהם יושמו."]),
            ("מגבלות ידועות", ["חלק ממסכי הניהול הוותיקים ורכיבי צד שלישי עשויים שלא לעמוד עדיין במלוא היעד. בשלב זה CareIL אינה מצהירה על הסמכה מלאה או על השלמת סקר נגישות רשמי."]),
            ("סיוע ומשוב", ["אם נתקלתם בחסם נגישות, פנו לכתובת הנגישות להלן וציינו עמוד, מכשיר ותיאור הבעיה. CareIL תפעל באופן סביר לספק חלופה נגישה ולתקן את התקלה."]),
        ]),
    },
    "refunds": {
        "en": _doc("Cancellation and Refund Policy", "This policy applies when CareIL offers paid subscriptions.", [
            ("Subscription cancellation", ["A subscription may be cancelled through the available account or billing controls or by contacting support. Unless mandatory law requires otherwise, cancellation prevents the next renewal and access continues until the end of the paid billing period."]),
            ("Refunds", ["Refund eligibility will be shown at purchase and will comply with mandatory consumer law. Duplicate charges, billing errors and legally required refunds will be corrected. Requests should include the account email, charge date and reason, but never client clinical information."]),
            ("Data after cancellation", ["Cancelling payment does not itself request immediate data deletion. Users should export required information and use the Danger Zone only when they intend to delete the complete workspace, subject to the 24-hour recovery window."]),
        ]),
        "he": _doc("מדיניות ביטול והחזרים", "מדיניות זו תחול כאשר CareIL תציע מנויים בתשלום.", [
            ("ביטול מנוי", ["ניתן לבטל מנוי בכלי החשבון או החיוב הזמינים או בפנייה לתמיכה. אלא אם דין מחייב קובע אחרת, הביטול מונע את החידוש הבא והגישה נמשכת עד סוף תקופת החיוב ששולמה."]),
            ("החזרים", ["הזכאות להחזר תוצג בעת הרכישה ותכובד בהתאם לדיני צרכנות קוגנטיים. חיוב כפול, טעות חיוב והחזר הנדרש בדין יתוקנו. יש לציין דוא״ל חשבון, מועד חיוב וסיבה, אך לא למסור מידע קליני של לקוחות."]),
            ("מידע לאחר ביטול", ["ביטול תשלום אינו בקשת מחיקת מידע. יש לייצא מידע נדרש ולהשתמש באזור הסכנה רק כאשר מבקשים למחוק את סביבת העבודה כולה, בכפוף לחלון שחזור של 24 שעות."]),
        ]),
    },
    "subprocessors": {
        "en": _doc("Subprocessors", "CareIL uses the following providers to operate the service. Optional providers process data only when the related feature is enabled.", [
            ("Railway", ["Purpose: application hosting, networking and persistent storage. Data: account and tenant data required to operate CareIL. Processing locations depend on the selected Railway deployment region and provider infrastructure."]),
            ("Resend", ["Purpose: transactional email delivery and delivery diagnostics. Data: recipient email address, message content and delivery metadata. Therapists should avoid placing unnecessary clinical details in email."]),
            ("Google", ["Purpose: optional Google Calendar OAuth and event synchronization. Data: authorization tokens and event information selected by CareIL. Google is used only after the therapist connects an account."]),
            ("Changes", ["CareIL will update this page before or when a material subprocessor change takes effect and will identify the current document version. Questions or legally grounded objections may be sent to the privacy contact."]),
        ]),
        "he": _doc("ספקי משנה", "CareIL משתמשת בספקים הבאים להפעלת השירות. ספק אופציונלי מעבד מידע רק כאשר התכונה הרלוונטית מופעלת.", [
            ("Railway", ["מטרה: אירוח היישום, תקשורת ואחסון מתמשך. מידע: פרטי חשבון וסביבת מטפל הדרושים להפעלת CareIL. מיקום העיבוד תלוי באזור הפריסה שנבחר ובתשתית הספק."]),
            ("Resend", ["מטרה: משלוח דוא״ל תפעולי ואבחון מסירה. מידע: כתובת נמען, תוכן הודעה ונתוני מסירה. יש להימנע מהכללת פרטים קליניים שאינם דרושים בדוא״ל."]),
            ("Google", ["מטרה: הרשאת Google Calendar וסנכרון אירועים אופציונליים. מידע: אסימוני הרשאה ופרטי אירוע שנבחרו על-ידי CareIL. השימוש מתחיל רק לאחר שהמטפל מחבר חשבון."]),
            ("שינויים", ["CareIL תעדכן עמוד זה לפני או בעת כניסת שינוי מהותי לתוקף ותציין את גרסת המסמך. שאלות או התנגדות המבוססת על דין ניתן לשלוח לכתובת הפרטיות."]),
        ]),
    },
    "security": {
        "en": _doc("Security and Data Retention", "This page summarizes current safeguards and operational limits. It is not a certification or guarantee of absolute security.", [
            ("Current safeguards", ["HTTPS in production; salted password hashing; secure cookie settings; tenant-separated SQLite databases; encrypted Google refresh tokens; short-lived one-time portal links; filename controls; limited demo capabilities; and application logging."]),
            ("User responsibilities", ["Therapists must protect credentials and devices, use unique passwords, keep contact details current, grant access only to authorized people, review exported information, and promptly report suspected unauthorized access."]),
            ("Retention and deletion", ["Active tenant information is retained while the account is active. Danger Zone requests suspend access and provide 24 hours to restore. At or after expiry, CareIL removes the tenant database and tenant upload directory during lifecycle cleanup. Legal, fraud-prevention or narrowly limited provider records may have different retention periods."]),
            ("Incident reporting", ["Suspected security issues should be sent to the security contact without including client clinical information. CareIL will investigate and make notifications required by applicable law according to its role."]),
        ]),
        "he": _doc("אבטחת מידע ושמירת נתונים", "עמוד זה מסכם אמצעי הגנה ומגבלות תפעוליות נוכחיים. הוא אינו הסמכה או הבטחה לאבטחה מוחלטת.", [
            ("אמצעי הגנה נוכחיים", ["HTTPS בייצור; גיבוב סיסמאות עם salt; הגדרות עוגייה מאובטחות; מסדי SQLite נפרדים למטפלים; הצפנת אסימוני Google; קישורי פורטל חד-פעמיים וקצרי תוקף; בקרת שמות קבצים; הגבלת יכולות הדגמה; ויומני יישום."]),
            ("אחריות המשתמש", ["על המטפל להגן על סיסמאות ומכשירים, להשתמש בסיסמה ייחודית, לעדכן פרטי קשר, לאפשר גישה רק למורשים, לבדוק מידע שיוצא מהמערכת ולדווח במהירות על חשד לגישה לא מורשית."]),
            ("שמירה ומחיקה", ["מידע נשמר כל עוד החשבון פעיל. בקשת אזור הסכנה משעה את הגישה ומאפשרת שחזור במשך 24 שעות. לאחר מכן CareIL מסירה את מסד המטפל ותיקיית הקבצים בתהליך התחזוקה. רישומים משפטיים, מניעת הונאה או רישומי ספק מוגבלים עשויים להישמר לתקופות שונות."]),
            ("דיווח אירוע", ["יש לשלוח חשד לבעיית אבטחה לכתובת האבטחה בלי לכלול מידע קליני של לקוחות. CareIL תבדוק ותבצע דיווחים הנדרשים בדין בהתאם לתפקידה."]),
        ]),
    },
}

