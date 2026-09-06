# חיבור webhook של Morning לחיובי CareIL

הגרסה הזו מוסיפה את הנתיב:

`https://www.careil.net/api/webhooks/morning`

## משתני Railway

```text
MORNING_CLIENT_ID=<API Key ID>
MORNING_CLIENT_SECRET=<Secret>
MORNING_API_BASE_URL=https://api.morning.co
MORNING_WEBHOOK_SECRET=<ערך אקראי ארוך ונפרד>
```

`MORNING_WEBHOOK_SECRET` אינו ה-API Secret. יש ליצור עבורו ערך אקראי חדש,
לשמור אותו ב-Railway ולהזין את אותו ערך בשדה Secret של ה-webhook ב-Morning.

## הגדרת Morning לאחר הפריסה

1. אזור אישי > כלים למפתחים > Webhooks > הוספה.
2. URL: `https://www.careil.net/api/webhooks/morning`
3. Secret: אותו ערך שהוגדר ב-`MORNING_WEBHOOK_SECRET`.
4. Event: `payment/received`.

CareIL מאמתת את חתימת `x-webhook-signature` על גוף הבקשה המקורי. האירוע
מתקבל רק כאשר הוא כולל `custom.careil_order_id`, והסכום, המטבע והמייל תואמים
להזמנה המקומית. טיפול חוזר באותה מסירה או עסקה אינו יוצר מנוי נוסף.

## מגבלה לפני עסקת בדיקה

ה-webhook מוכן, אך עמוד התשלום עדיין אינו יוצר בקשת תשלום ב-Morning. לשם כך
נדרשת נקודת יצירת התשלום/דף המכירה שאושרה בחשבון Morning Pay, עם אפשרות להעביר
את `custom.careil_order_id`. אין לבצע עסקת ניסיון לפני חיבור שלב זה.
