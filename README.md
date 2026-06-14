<img width="150" height="148" alt="שדג" src="https://github.com/user-attachments/assets/93be22a1-8343-4c03-95df-3aed93bc23d0" />

![Build Status](https://github.com/ACHI-GARCINAN/Talmud-Formulas-Software/actions/workflows/main.yml/badge.svg)

# נוסחאות התלמוד

**נוסחאות התלמוד** הינה תוכנה המיועדת להצגת שינויי נוסחאות בין מהדורות והוצאות שונות של דפי הגמרא.

## אודות הפרויקט
התוכנה מאפשרת עיון והשוואה בין עדי נוסח שונים בצורה נוחה וידידותית, תוך דגש על חוויית משתמש חלקה.

### התוכנה מבוססת על פרוייקט "הכי גרסינן" של דב פרידברג - שנמצאת היום תחת חסותה של "הספריה הלאומית" וניתן להיכנס לאתר שלהם - [כאן](https://fjms.genizah.org/?eraseCache=true)

## **שיפורים שיש בתוכנה כרגע (מתעדכן, בעז"ה):**

- **כל הש"ס אופליין**: אין צורך בחיבור לאינטרנט, הכל נמצא בתוך התוכנה.

- **השוואה חכמה**: סימון והדגשה של מילים חסרות, יתירות או שונות בהשוואה לנוסח המייצג.

- **מצב תצוגת מילים** - נוספה אפשרות לתצוגת מילים - כך אפשר לעבור מילה מילה ולערוך השוואה מדוייקת יותר בין הנוסחאות

- **ממשק מודרני**: עיצוב נקי ונוח לעין, תמיכה מלאה בעברית, גלילה מותאמת למסכי מגע.

- **ערכות נושא** - ישנה תמיכה בשני ערכות נושא לתוכנה

- **חיפוש מהיר**: ניווט קל בין מסכתות ודפים.

- **צמצום חלונית הניווט** - נוסף כפתור לצימצום תצוגת הניווט - לנוחות קריאה ושימוש
- **תמיכה בגופנים** - התוכנה תומכת בכל הגופנים בעברית המותקנים במחשב.

- **מסכי מגע** - התוכנה תומכת במסכי מגע (- לא באופן מלא, בטיפול)

- **מצב תצוגת קריאה** - לנוחות קריאה בטקסט הגמרא - ללא חלוקה גמורה למקטעים

- **הסתרת תיקוני קיצורים** - נוסף כפתור להסתרת הבדלי נוסח שאינם משמעותיים בדרך כלל - כגון עי' = עיין. וכדומה.

## למעבר לאתר ההורדה כנסו [כאן](https://achi-garcinan.github.io/ACHI-GARCINAN/#download)


## על פרויקט "הכי גרסינן"
"במימונו של דב פרידברג הוקם פרויקט **הכי גרסינן**, הכולל בתוכו את רוב רובם של כתבי היד שמוכרים כיום על התלמוד. הכל מסודר ומתוייק, בצורה שעל כל מילה בתלמוד בבלי אפשר לראות את כל עדי הנוסח לפי שמותם."

---

**פרויקט זה נועד להנגיש את אוצרות הרוח של חכמי ישראל ללומדי התורה ולחוקריה**

---

## התקנה

להתקין את התלויות הנדרשות מתוך הקובץ `requirements.txt`:

```bash
pip install -r requirements.txt
```

## הרצה מקומית

להריץ את התוכנה בסביבת פיתוח מקומית תוך שימוש ב-virtualenv:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix / macOS
# source .venv/bin/activate

pip install -r requirements.txt

# הפעלת התוכנה (אם `talmud.db` נמצא בתיקייה הנוכחית):
python main.py

# או להפנות לתיקייה שבה קובץ talmud.db נמצא:
python main.py "C:\\path\\to\\folder\\with\\talmud.db"
```

### בדיקות מהירות (smoke test)

הרצת סקריפט בדיקה מהיר שמודד טעינה בסיסית של הממשק (לא פותח את הלולאה הראשית):

```bash
python run_smoke.py
```

## PyInstaller — build מקומי (דוגמאות)

Windows (onedir):

```bash
pyinstaller --noconfirm --onedir --windowed \
	--icon=icon.ico \
	--name="TalmudicFormulas" \
	--add-data "talmud.db;." \
	--add-data "widgets;widgets" \
	--add-data "assets;assets" \
	main.py
```

macOS (universal):

```bash
pyinstaller --noconfirm --windowed --target-architecture universal2 \
	--name "TalmudicFormulas" \
	--add-data "talmud.db:." \
	--add-data "widgets:widgets" \
	--add-data "assets:assets" \
	main.py
```

> הערה: ודא שאתה מריץ את PyInstaller מאותה סביבת Python שבה התקנת את `requirements.txt`. לבניית installers עבור פלטפורמה שאינה מקומית (למשל בניית Windows על macOS) יש להשתמש ב-runner מתאים או במכונה וירטואלית.

## תיעוד מסד נתונים

תיאור סכמת מסד הנתונים של הפרויקט זמין ב-[docs/DB_SCHEMA.md](docs/DB_SCHEMA.md).

---

## הורדת התוכנה
הקישורים הבאים תמיד יורידו את הגרסה האחרונה ביותר שיצאה:

* **[להורדת גרסת התקנה (Setup)](https://github.com/ACHI-GARCINAN/ACHI-GARCINAN/releases/latest/download/Talmud-Formulas-Setup.exe)**

* **[להורדת גרסה ניידת - ללא התקנה (Portable)](https://github.com/ACHI-GARCINAN/ACHI-GARCINAN/releases/latest/download/Talmud-Formulas.exe)**
