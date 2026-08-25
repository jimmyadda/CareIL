(function () {
  "use strict";

  var UI_TEXT = [
    ["Home", "בית"], ["Clients", "מטופלים"], ["Schedule", "פגישות"], ["Settings", "הגדרות"],
    ["Main navigation", "ניווט ראשי"], ["Appointments", "פגישות"], ["Appointment", "פגישה"],
    ["Book appointment", "קביעת פגישה"], ["Book Appointment", "קביעת פגישה"], ["Calendar view", "תצוגת יומן"], ["Calendar View", "תצוגת יומן"],
    ["Client", "מטופל"], ["Client Name", "שם המטופל"], ["Appointment Date", "תאריך פגישה"], ["Appointment date", "תאריך פגישה"],
    ["Delete", "מחק"], ["Edit", "ערוך"], ["Approve", "אישור"], ["Approve appointment", "אישור פגישה"],
    ["Close", "סגור"], ["Save", "שמור"], ["Save changes", "שמור שינויים"], ["Submit", "שליחה"], ["Cancel", "ביטול"],
    ["Search:", "חיפוש:"], ["Search", "חיפוש"], ["Show", "הצג"], ["entries", "רשומות"],
    ["No data available in table", "אין נתונים בטבלה"], ["No matching records found", "לא נמצאו רשומות תואמות"],
    ["Previous", "הקודם"], ["Next", "הבא"], ["Processing...", "מעבד..."],
    ["Booking availability", "זמינות לקביעת פגישות"], ["Back to settings", "חזרה להגדרות"],
    ["When clients may book", "מתי מטופלים יכולים לקבוע פגישה"], ["Existing appointments are automatically excluded.", "פגישות קיימות נחסמות אוטומטית."],
    ["Available days", "ימים זמינים"], ["Sunday", "יום ראשון"], ["Monday", "יום שני"], ["Tuesday", "יום שלישי"],
    ["Wednesday", "יום רביעי"], ["Thursday", "יום חמישי"], ["Friday", "יום שישי"], ["Saturday", "שבת"],
    ["Start time", "שעת התחלה"], ["End time", "שעת סיום"], ["Session duration", "משך פגישה"], ["Save availability", "שמירת זמינות"],
    ["Google Calendar connected successfully.", "יומן Google חובר בהצלחה."], ["Google Calendar disconnected.", "יומן Google נותק."],
    ["Connected", "מחובר"], ["Confirmed appointments sync to your primary Google Calendar.", "פגישות מאושרות מסתנכרנות עם יומן Google הראשי שלך."],
    ["Sync upcoming appointments", "סנכרון פגישות קרובות"], ["Sync Google Calendar", "סנכרון יומן Google"], ["Disconnect", "ניתוק"],
    ["Connect Google Calendar", "חיבור יומן Google"], ["Google Calendar credentials are not configured yet.", "פרטי החיבור ליומן Google עדיין לא הוגדרו."],
    ["Update Clinic Information", "עדכון פרטי הקליניקה"], ["Clinic Name", "שם הקליניקה"], ["Address", "כתובת"], ["Phone", "טלפון"],
    ["Email", "דוא״ל"], ["Website (optional)", "אתר (לא חובה)"], ["Mail Settings", "הגדרות דוא״ל"], ["Mail Server", "שרת דוא״ל"],
    ["Mail Port", "יציאת דוא״ל"], ["Use TLS", "שימוש ב־TLS"], ["True", "כן"], ["False", "לא"], ["Mail Username", "שם משתמש לדוא״ל"],
    ["Mail Password", "סיסמת דוא״ל"], ["Save Settings", "שמירת הגדרות"], ["Send message to client", "שליחת הודעה למטופל"], ["Subject", "נושא"],
    ["Full name", "שם מלא"], ["Actions", "פעולות"], ["Client Appointments", "פגישות המטופל"],
    ["minutes", "דקות"], ["Table view", "תצוגת טבלה"], ["Admin Panel", "הגדרות הקליניקה"],
    ["Update Clinic Info", "עדכון פרטי הקליניקה"], ["Manage and update clinic details such as name, address, and contact info.", "ניהול ועדכון שם הקליניקה, הכתובת ופרטי הקשר."],
    ["Configure Mail Settings", "הגדרת דוא״ל"], ["Configure email settings for appointment notifications and other communications.", "הגדרת הדוא״ל להתראות על פגישות ולתקשורת נוספת."],
    ["Booking Availability", "זמינות לקביעת פגישות"], ["Choose the days, hours and duration clients can request online.", "בחירת הימים, השעות ומשך הפגישה שמטופלים יכולים לבקש אונליין."],
    ["Manage Availability", "ניהול זמינות"], ["Therapist Profile", "פרופיל המטפל"], ["Update the single therapist name and contact information.", "עדכון שם המטפל היחיד ופרטי הקשר."],
    ["Edit Therapist Profile", "עריכת פרופיל המטפל"], ["Automatically synchronize confirmed appointments with the therapist’s calendar.", "סנכרון אוטומטי של פגישות מאושרות עם יומן המטפל."],
    ["Calendar Sync", "סנכרון יומן"], ["Danger Zone", "אזור מסוכן"], ["Manage Account Deletion", "ניהול מחיקת החשבון"],
    ["Suspend and permanently delete your CareIL workspace, with a 24-hour recovery period.", "השהיה ומחיקה לצמיתות של סביבת CareIL, עם אפשרות שחזור למשך 24 שעות."],
    ["Legal & Privacy", "משפטי ופרטיות"], ["Review CareIL privacy, service terms, data processing and security information.", "עיון במדיניות הפרטיות, תנאי השירות, עיבוד הנתונים ואבטחת המידע של CareIL."],
    ["View Legal Documents", "הצגת מסמכים משפטיים"], ["Are you sure?", "האם אתם בטוחים?"],
    ["You will not be able to recover this data", "לא ניתן יהיה לשחזר את הנתונים"], ["Yes, delete it!", "כן, למחוק"],
    ["Deleted!", "נמחק"], ["Appointment has been deleted.", "הפגישה נמחקה."], ["Appointment Request has been deleted.", "בקשת הפגישה נמחקה."],
    ["Add session summary", "הוספת סיכום פגישה"], ["Date", "תאריך"], ["Description", "תיאור"], ["Desc", "תיאור"],
    ["Write session summary", "כתיבת סיכום פגישה"], ["Summary types", "סוגי סיכום"], ["Add Type", "הוספת סוג"],
    ["Save Template", "שמירת תבנית"], ["Load Template", "טעינת תבנית"]
    ,["Please select Client", "בחרו מטופל"], ["Select a client", "בחרו מטופל"], ["Write something..", "כתבו הודעה..."],
    ["Connect the therapist’s Google account. CareIL will create calendar events only for confirmed appointments.", "חברו את חשבון Google של המטפל. CareIL תיצור אירועים ביומן רק עבור פגישות מאושרות."],
    ["Create a Google Cloud OAuth Web Application, enable the Google Calendar API and add this authorized redirect URI:", "צרו יישום OAuth מסוג Web ב־Google Cloud, הפעילו את Google Calendar API והוסיפו את כתובת ההפניה המאושרת הבאה:"],
    ["Then set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your environment and restart Flask.", "לאחר מכן הגדירו את GOOGLE_CLIENT_ID ואת GOOGLE_CLIENT_SECRET במשתני הסביבה והפעילו מחדש את Flask."]
  ];

  function currentLanguage() {
    return sessionStorage.getItem("lang") === "HE" ? "HE" : "EN";
  }

  function translatedText(value) {
    var language = currentLanguage();
    var trimmed = String(value || "").trim();
    var match;
    for (var i = 0; i < UI_TEXT.length; i += 1) {
      if (trimmed === UI_TEXT[i][0] || trimmed === UI_TEXT[i][1]) return language === "HE" ? UI_TEXT[i][1] : UI_TEXT[i][0];
    }
    match = trimmed.match(/^Showing\s+(\d+)\s+to\s+(\d+)\s+of\s+(\d+)\s+entries$/i);
    if (match) return language === "HE" ? "מציג " + match[1] + " עד " + match[2] + " מתוך " + match[3] + " רשומות" : trimmed;
    match = trimmed.match(/^מציג\s+(\d+)\s+עד\s+(\d+)\s+מתוך\s+(\d+)\s+רשומות$/);
    if (match) return language === "EN" ? "Showing " + match[1] + " to " + match[2] + " of " + match[3] + " entries" : trimmed;
    match = trimmed.match(/^(\d+)\s+minutes$/i);
    if (match) return language === "HE" ? match[1] + " דקות" : trimmed;
    match = trimmed.match(/^(\d+)\s+דקות$/);
    if (match) return language === "EN" ? match[1] + " minutes" : trimmed;
    return null;
  }

  function translateElement(element) {
    Array.prototype.forEach.call(element.childNodes || [], function (node) {
      if (node.nodeType !== 3 || !node.nodeValue.trim()) return;
      var replacement = translatedText(node.nodeValue);
      if (replacement && replacement !== node.nodeValue.trim()) {
        node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), replacement);
      }
    });
    ["placeholder", "title", "aria-label"].forEach(function (attribute) {
      if (!element.hasAttribute || !element.hasAttribute(attribute)) return;
      var replacement = translatedText(element.getAttribute(attribute));
      if (replacement) element.setAttribute(attribute, replacement);
    });
    if (element.tagName === "INPUT" && (element.type === "submit" || element.type === "button")) {
      var valueReplacement = translatedText(element.value);
      if (valueReplacement) element.value = valueReplacement;
    }
  }

  function localizePage() {
    var language = currentLanguage();
    document.documentElement.lang = language === "HE" ? "he" : "en";
    document.documentElement.dir = language === "HE" ? "rtl" : "ltr";
    if (document.body) {
      document.body.classList.toggle("clinic-lang-he", language === "HE");
      document.body.classList.toggle("clinic-lang-en", language !== "HE");
    }
    document.querySelectorAll("h1,h2,h3,h4,h5,label,button,a,th,option,p,strong,.content-heading,.card-title,.card-text,.dataTables_info,.dataTables_empty,.dataTables_filter,.dataTables_length,.paginate_button,.alert,input[placeholder],textarea[placeholder],input[type=submit],input[type=button]").forEach(translateElement);
  }

  window.CareILI18n = {
    language: currentLanguage,
    text: function (en, he) { return currentLanguage() === "HE" ? he : en; },
    refresh: localizePage
  };

  function addBrandMetadata() {
    if (!document.querySelector('link[rel="icon"]')) {
      var favicon = document.createElement("link");
      favicon.rel = "icon";
      favicon.href = "/static/favicon.ico?v=1";
      document.head.appendChild(favicon);
    }
    if (!document.querySelector('link[rel="apple-touch-icon"]')) {
      var touchIcon = document.createElement("link");
      touchIcon.rel = "apple-touch-icon";
      touchIcon.href = "/static/img/apple-touch-icon.png?v=1";
      document.head.appendChild(touchIcon);
    }
  }

  function addMobileNavigation() {
    if (!document.body || document.querySelector(".clinic-bottom-nav")) return;
    var path = window.location.pathname;
    var items = [
      ["/", "fa-home", "Home", "בית"],
      ["/patient", "fa-users", "Clients", "מטופלים"],
      ["/appointment", "fa-calendar", "Schedule", "פגישות"],
      ["/admin/adminPanel", "fa-cog", "Settings", "הגדרות"]
    ];
    var nav = document.createElement("nav");
    nav.className = "clinic-bottom-nav";
    nav.setAttribute("aria-label", currentLanguage() === "HE" ? "ניווט ראשי" : "Main navigation");
    nav.innerHTML = items.map(function (item) {
      var active = item[0] === "/" ? path === "/" : path.indexOf(item[0]) === 0;
      return '<a href="' + item[0] + '" class="' + (active ? "is-active" : "") + '">' +
        '<i class="fa ' + item[1] + '" aria-hidden="true"></i><span>' + (currentLanguage() === "HE" ? item[3] : item[2]) + "</span></a>";
    }).join("");
    document.body.appendChild(nav);
  }

  function applyMobileTableLabels(table) {
    var headers = Array.prototype.map.call(table.querySelectorAll("thead th"), function (header) {
      return header.textContent.trim();
    });
    if (!headers.length) return;

    table.classList.add("clinic-responsive-table");
    var isClientList = window.location.pathname === "/patient" && table.id === "datatable4";
    table.classList.toggle("clinic-client-list", isClientList);
    table.querySelectorAll("tbody tr").forEach(function (row) {
      var cells = row.querySelectorAll("td");
      cells.forEach(function (cell, index) {
        if (cell.classList.contains("dataTables_empty") || cell.colSpan > 1) {
          cell.classList.add("clinic-table-empty");
          cell.removeAttribute("data-label");
          return;
        }
        cell.classList.remove("clinic-table-empty");
        cell.setAttribute("data-label", headers[index] || "Actions");
      });

      if (isClientList && cells.length >= 2 && !cells[0].classList.contains("dataTables_empty")) {
        var language = sessionStorage.getItem("lang") || "EN";
        var fullNameLabel = window.Translate_jsonData && window.Translate_jsonData[language]
          ? window.Translate_jsonData[language].fullName
          : null;
        cells[0].classList.add("clinic-mobile-name");
        cells[0].setAttribute("data-label", fullNameLabel || "Full name");
        cells[0].setAttribute("data-mobile-full-name", (cells[0].textContent + " " + cells[1].textContent).trim());
        for (var hiddenIndex = 1; hiddenIndex <= 6 && hiddenIndex < cells.length; hiddenIndex += 1) {
          cells[hiddenIndex].classList.add("clinic-mobile-hidden");
        }
        for (var actionIndex = 7; actionIndex < cells.length; actionIndex += 1) {
          cells[actionIndex].classList.add("clinic-mobile-action");
        }
      }
    });
  }

  function refreshResponsiveTables() {
    document.querySelectorAll("table.table").forEach(function (table) {
      table.setAttribute("role", "table");
      applyMobileTableLabels(table);
    });
  }

  function improveTables() {
    refreshResponsiveTables();

    var observer = new MutationObserver(function () {
      refreshResponsiveTables();
    });
    document.querySelectorAll("table.table").forEach(function (table) {
      observer.observe(table, {childList: true, subtree: true, characterData: true});
    });

    document.querySelectorAll(".language-flag").forEach(function (button) {
      button.addEventListener("click", function () {
        window.setTimeout(refreshResponsiveTables, 0);
      });
    });
  }

  function markSingleTherapistFields() {
    document.querySelectorAll("#doctor_select").forEach(function (select) {
      var group = select.closest(".form-group");
      if (group) group.classList.add("single-therapist-field");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    addBrandMetadata();
    addMobileNavigation();
    improveTables();
    markSingleTherapistFields();
    localizePage();
    var localizeTimer;
    new MutationObserver(function () {
      window.clearTimeout(localizeTimer);
      localizeTimer = window.setTimeout(localizePage, 25);
    }).observe(document.body, {childList: true, subtree: true, characterData: true});
    document.querySelectorAll(".language-flag").forEach(function (button) {
      button.addEventListener("click", function () { window.setTimeout(localizePage, 20); });
    });
  });
})();
