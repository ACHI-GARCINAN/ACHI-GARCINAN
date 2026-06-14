# Database Schema Documentation

## Overview

הדוקומנטציה הזו מתארת את סכמת מסד הנתונים המשמשת את התוכנה.
היא מבוססת על הטבלאות והשאילתות שמופיעות בקוד המקור.

## טבלאות ראשיות

### masechtot
- `id` - מפתח ראשי
- `num` - מספר סדר של המסכת
- `name` - שם המסכת

### pages
- `id` - מפתח ראשי
- `masechet_id` - reference ל-`masechtot`
- `page_label` - תווית דף, למשל `דף נא`

### sections
- `id` - מפתח ראשי
- `page_id` - reference ל-`pages`
- `section_label` - שם הקטע בתוך הדף

### texts
- `id` - מפתח ראשי
- `section_id` - reference ל-`sections`
- `witness_id` - reference ל-`witnesses`
- `content` - טקסט המילה או המשפט לפי עד הנוסח

### witnesses
- `id` - מפתח ראשי
- `name` - שם העד הנוסח
- `position` - מיקום העד (למשל עד ראשי / עד משני)

### manuscript_info
- `id` - מפתח ראשי
- `witness_id` - reference ל-`witnesses`
- `name` - שם כתב היד
- `full_text` - פרטי כתב היד

### words
- `id` - מפתח ראשי
- `word` - המילה הייחודית

### sections_words
- `id` - מפתח ראשי
- `section_id` - reference ל-`sections`
- `page_id` - reference ל-`pages`

### sections_words_texts
- `id` - מפתח ראשי
- `sections_word_id` - reference ל-`sections_words`
- `witness_id` - reference ל-`witnesses`
- `word_id` - reference ל-`words`

## יחסים בין הטבלאות

- `masechtot` (1) ←→ (N) `pages`
- `pages` (1) ←→ (N) `sections`
- `sections` (1) ←→ (N) `texts`
- `witnesses` (1) ←→ (N) `texts`
- `words` (1) ←→ (N) `sections_words_texts`
- `sections_words` (1) ←→ (N) `sections_words_texts`

## שאילתות טיפוסיות

```sql
SELECT id, num, name
FROM masechtot
ORDER BY num;
```

```sql
SELECT name
FROM witnesses
WHERE masechet_id = ?
ORDER BY position;
```

```sql
SELECT id, page_label
FROM pages
WHERE masechet_id = ?
ORDER BY id;
```

```sql
SELECT w.name, t.content
FROM texts t
JOIN witnesses w ON w.id = t.witness_id
WHERE t.section_id = ?;
```

```sql
SELECT m.name, p.page_label, s.section_label
FROM texts t
JOIN witnesses w ON w.id = t.witness_id
JOIN sections s ON s.id = t.section_id
JOIN pages p ON p.id = s.page_id
JOIN masechtot m ON m.id = p.masechet_id
WHERE w.position = 0
AND ( ... );
```

## הערות

הסכמה הזו מיועדת לתיעוד הקשר בין טבלאות בסיס הנתונים שנמצאות בשימוש פעיל בקוד של התוכנה.
