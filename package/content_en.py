"""Public English educational content for CareIL.

Every article in this module must have a matching slug in content_he.py.
"""

ENGLISH_ARTICLES = {
    "nihul-klinika-pratit": {
        "title": "How to Manage a Private Practice Without Becoming Its Administrator",
        "description": "A practical guide for therapists who want to reduce administrative overload, organize their workday and preserve more attention for therapy.",
        "eyebrow": "Practice management", "reading_time": "6 min read",
        "intro": "A private practice is more than a sequence of sessions. Every appointment brings scheduling, notes, documents, payments and follow-up tasks. When information is scattered across calendars, messages and files, even a small action requires searching and remembering.",
        "sections": [
            ("The burden lives in the small transitions", ["Administrative overload is often created by dozens of small switches between the calendar, messages, client records, tasks and receipts. Each switch costs attention.", "A good practice-management system should quietly hold the organizational layer so the therapist can focus on the person in the room."]),
            ("Keep one reliable client record", ["Contact details, appointments, session summaries, documents, questionnaires and relevant tasks should be accessible from one client record.", "Availability and appointment requests should connect to the same source of truth, reducing duplicate entry and avoidable mistakes."]),
            ("Create a short end-of-session routine", ["A consistent routine can include three actions: note the main points, record the next task and confirm the next appointment.", "Keep operational tasks separate from clinical notes so a reminder to call a parent does not disappear inside a long summary."]),
            ("Automate selectively", ["Calendar synchronization and receipt creation can save time, but decisions such as accepting an appointment request should remain under the therapist's control.", "CareIL brings records, appointments, requests, questionnaires and documents into one Hebrew-and-English workspace."]),
        ],
        "takeaways": ["One record per client", "A short closing routine", "Separate notes from tasks", "Automate without losing professional control"],
    },
    "tiud-tipuli-digitali": {
        "title": "Digital Therapy Notes: Staying Organized While Protecting Privacy",
        "description": "Practical principles for digital clinical documentation, including access, temporary links, data separation and responsible work habits.",
        "eyebrow": "Documentation and privacy", "reading_time": "7 min read",
        "intro": "Digital documentation can make practice work easier to organize and retrieve, but convenience must be paired with deliberate privacy practices. Responsibility extends beyond choosing a password to deciding what is collected, shared and retained.",
        "sections": [
            ("Keep only what is necessary", ["Collect and retain only information needed for a clear professional purpose. A longer form is not automatically a better form.", "Separating contact, operational and clinical information makes access easier to manage and limits unnecessary exposure."]),
            ("Prefer personal, time-limited access", ["Documents and questionnaires should be available to the intended person for a limited period. A revocable, expiring link is safer than a permanent public link.", "CareIL portal links are associated with a specific client, expire and can be revoked; therapists should still verify contact details before sending."]),
            ("Work habits matter", ["No system can compensate for shared passwords, unlocked devices or copying sensitive material into inappropriate channels.", "Use a unique password, device locking and two-factor authentication, and avoid revealing unnecessary names in external calendar titles or lock-screen notifications."]),
            ("Prepare for mistakes", ["Know how to revoke a link, change a password and contact support if information is sent to the wrong recipient or a device is lost.", "This article is general information, not legal or professional advice. Each practice must assess the requirements that apply to it."]),
        ],
        "takeaways": ["Minimize stored data", "Use expiring links", "Protect accounts and devices", "Have a response plan"],
    },
    "nihul-yoman-torim": {
        "title": "Managing Appointments and Requests Without Double Booking",
        "description": "Build a clear flow from appointment request to approval while keeping control of availability and calendar synchronization.",
        "eyebrow": "Calendar and appointments", "reading_time": "5 min read",
        "intro": "Appointment coordination quickly becomes a chain of messages about availability, confirmation and calendar updates. A clear process should be convenient for clients while leaving the final decision with the therapist.",
        "sections": [
            ("Define availability first", ["Set working days, hours and session duration before showing options. Clients should see only times inside practice hours that do not conflict with existing appointments.", "Pending requests should temporarily hold a slot so several people cannot select it at once."]),
            ("A request is not yet an appointment", ["Use three clear states: pending, approved and declined. Until approval, the request should not appear as a confirmed external-calendar event.", "After approval, create the appointment, synchronize it when enabled and send the client the exact date and time."]),
            ("Maintain one source of truth", ["When a session is entered manually in several places, it becomes difficult to know which calendar is current. Manage the appointment in one central system and synchronize from there.", "CareIL checks portal requests against availability, confirmed sessions and pending requests."]),
            ("Send only useful information", ["A confirmation should state the date, start time, end time and a simple calendar option, without including clinical information.", "A short and consistent process reduces messages and makes pending decisions easy to spot."]),
        ],
        "takeaways": ["Show genuinely available times", "Hold pending requests", "Separate requests from appointments", "Synchronize from one source"],
    },
    "tipul-rigshi-klinika": {
        "title": "Emotional Therapy in Private Practice: The Structure Around the Session",
        "description": "A guide for emotional therapists on organizing appointments, documentation, communication and privacy around clinical work.",
        "eyebrow": "Emotional therapy", "reading_time": "5 min read",
        "intro": "Emotional therapy rests first on the relationship in the room. Around each session, however, therapists manage scheduling, documentation, parent communication, questionnaires, documents and payments. A well-organized structure supports continuity without taking over the work.",
        "sections": [
            ("Keep the session at the center", ["Clinical presence is demanding, while small administrative tasks accumulate throughout the day.", "One central place for client details, appointments and documents reduces searching and duplicate entry without replacing professional judgment."]),
            ("Support continuity between sessions", ["Continuity also depends on knowing what happened recently, what follow-up was agreed and whether a document or questionnaire requires attention.", "A brief end-of-session routine is more reliable than reconstructing a week of work from memory."]),
            ("Communicate clearly and minimally", ["Operational messages should contain only what is required for the action and should not include clinical content.", "When working with children and parents, decide in advance who receives each message and verify the recipient before sending."]),
            ("Pair organization with privacy", ["Use personal accounts, two-factor authentication, appropriate permissions and data minimization.", "CareIL is designed to organize records, appointments, questionnaires, documents and payments; each practice remains responsible for its professional and legal obligations."]),
        ],
        "takeaways": ["Centralize the operational layer", "Use a short closing routine", "Separate clinical and operational communication", "Combine convenience with privacy"],
    },
    "hadrachat-horim-ma-ze": {
        "title": "Parent Guidance: What It Is, Who It Helps and What to Expect",
        "description": "A guide to the purpose of parent guidance, when it may help, how meetings work and how insight becomes everyday change at home.",
        "eyebrow": "Parent guidance", "reading_time": "6 min read",
        "intro": "Parent guidance is a professional space for pausing, understanding what is happening at home and exploring responses that fit the child and family. It is not a lesson in perfect parenting or a fixed list of instructions, but a collaborative process.",
        "sections": [
            ("When parent guidance may help", ["Parents seek support around outbursts, separation, boundaries, sibling jealousy, fears, family changes or communication that has become tense and exhausting.", "Guidance can stand alone or accompany a child's emotional therapy, depending on age, needs and the role of the home environment."]),
            ("What happens in a meeting", ["The first stage maps the concern, when it appears, what has been tried and what happens before and after difficult moments.", "Together, the therapist and parents choose one manageable focus, try a response or routine at home and review what happened."]),
            ("Understanding and limits can coexist", ["Accepting a feeling does not mean accepting every behavior. A parent can recognize anger or disappointment while stopping harm and maintaining a necessary boundary.", "Empathy plus a clear message shows the child that they are seen and that an adult can safely hold the situation."]),
            ("Recognizing progress", ["Early progress may appear as quicker understanding, less escalation or faster recovery rather than the complete disappearance of difficulty.", "Parent guidance does not replace medical or mental-health assessment when there is danger, significant impairment or continuing deterioration."]),
        ],
        "takeaways": ["Choose one focus", "Look before and after the difficulty", "Combine empathy and boundaries", "Notice small changes in connection and response"],
    },
    "gvulot-im-empatia": {
        "title": "Setting Boundaries With Empathy: Clear Limits Without a Power Struggle",
        "description": "Practical guidance for calm and consistent boundaries, responding to resistance and reducing power struggles at home.",
        "eyebrow": "Parent guidance", "reading_time": "5 min read",
        "intro": "A boundary is not designed to defeat a child. It protects the child, other people and a daily routine everyone can rely on. Children may be angry about a necessary limit; the goal is to communicate it clearly and accompany the feeling it creates.",
        "sections": [
            ("A useful limit begins with an adult decision", ["Before setting a limit, check that it matters, fits the child's age and can be maintained. A few important rules are stronger than many prohibitions.", "State briefly what cannot happen and what is possible instead. Long explanations during distress often turn into negotiation."]),
            ("Name the feeling and keep the rule", ["You can acknowledge that stopping play is disappointing while still leading the transition to bath time.", "If the child hits, throws or creates danger, stop the action first. Leave teaching and discussion until bodies are calmer."]),
            ("Offer choice inside the frame", ["A small choice can restore influence without handing over an adult decision: walk to the room alone or together, use the boat or the cup in the bath.", "Not every moment requires a choice. When immediate action is needed, clear and calm leadership is better than a question the child cannot truly refuse."]),
            ("When the boundary keeps failing", ["Consider tiredness, hunger, abrupt transitions, inconsistency between adults or an unintended reward for resistance.", "Consistency is not rigidity. Parents can repair after shouting and try again while keeping the limit. Frequent or harmful struggles may benefit from professional guidance."]),
        ],
        "takeaways": ["Choose a few important limits", "Keep the message short", "Accept feelings and stop harm", "Offer only genuine choices"],
    },
    "hitmodedut-im-hitpartsuyot": {
        "title": "Children's Emotional Outbursts: What They Communicate and How Parents Can Respond",
        "description": "Understand overload and triggers, respond safely during an outburst and support regulation after the child calms down.",
        "eyebrow": "Parent guidance", "reading_time": "6 min read",
        "intro": "An outburst is a moment when the demands on a child exceed their current ability to regulate. The behavior requires a firm limit when there is danger, while longer-term change begins with understanding what preceded it and what skill the child still needs.",
        "sections": [
            ("Look for the sequence, not only the explosion", ["Notice what happened before: a transition, fatigue, hunger, loss, sensory load or an unmet expectation. Brief notes across several events can reveal a pattern.", "Understanding a trigger does not mean preventing all frustration. It helps adults prepare the child and teach skills during calm moments."]),
            ("During the outburst: fewer words, more presence", ["A flooded child has limited capacity for explanations. Speak slowly, reduce stimulation and maintain a safe distance.", "If there is danger, stop the action and move objects or people as needed. A simple message is enough: I am here; I will not let you hurt; we will talk when your body is calmer."]),
            ("Afterwards: reconnect and learn", ["Briefly describe what happened, name the feeling and consider one option for next time. Match the conversation to the child's age and avoid turning it into an interrogation.", "If someone was hurt, support a practical repair such as checking on them or helping restore what was damaged."]),
            ("When to seek help", ["Consult a professional when outbursts are very frequent, prolonged, worsening, occur across settings or significantly affect relationships and functioning.", "Seek prompt support when there is self-harm, danger to others or difficulty maintaining safety. Guidance may be combined with developmental, emotional or medical assessment."]),
        ],
        "takeaways": ["Identify what came before", "Use fewer words during overload", "Protect safety first", "Reconnect and teach after calm returns"],
    },
}


ENGLISH_FAQ = [
    ("What is CareIL?", "CareIL is an Israeli practice-management system for independent therapists. It brings client information, appointments, session summaries, questionnaires, documents and tasks into one workspace."),
    ("Who is CareIL designed for?", "CareIL is designed for independent emotional therapists, psychologists, arts therapists, parent-guidance professionals and other care providers managing a private practice."),
    ("Can I use CareIL in English?", "Yes. CareIL includes Hebrew and English interfaces and is designed for desktop and mobile use."),
    ("Does CareIL synchronize with Google Calendar?", "Yes. After connecting Google, approved appointments can synchronize with the calendar. Pending requests do not become calendar appointments until the therapist approves them."),
    ("How can a client request an appointment?", "The therapist sends a portal link. The client selects an available time and submits a request, which the therapist can approve or decline."),
    ("Can I send questionnaires and documents?", "Yes. Therapists can create questionnaires, reuse templates and share them through a time-limited client portal link. Responses return to the client record."),
    ("Can CareIL issue receipts?", "CareIL can connect to the practice's Morning account and issue a receipt from a completed appointment. The document also remains available in Morning."),
    ("How does CareIL approach privacy?", "CareIL includes separate practice environments, account authentication and short-lived portal links that can be revoked. Secure use also depends on the practice's settings and work habits."),
    ("Is there a demo?", "Yes. You can open a demonstration workspace without entering real client information. Demo workspaces expire automatically."),
    ("How do I join CareIL?", "Submit an access request on the website. After approval, you receive a personal, time-limited link for creating the practice account."),
]
