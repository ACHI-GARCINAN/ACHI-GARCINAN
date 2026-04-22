; קובץ הגדרות עבור Inno Setup - Talmudic Formulas
; -----------------------------------------------

[Setup]
; הגדרות בסיסיות של התוכנה
AppName=Talmudic Formulas
AppVersion=1.1
DefaultDirName={autopf}\Talmudic Formulas
DefaultGroupName=Talmudic Formulas
OutputDir=Output
OutputBaseFilename=Talmudic-Formulas-Setup-Win
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes

; חלוניות אישור ומידע (משתמש בקבצים מהתיקייה הראשית שלך)
LicenseFile=license.txt
InfoBeforeFile=comments.txt

; הגדרות שפה - מאפשר למשתמש לבחור שפה בעת ההפעלה
ShowLanguageDialog=yes

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. העתקת כל תוכן התיקייה המפורקת (כולל talmud.db ו-assets)
; הנתיב dist\Talmudic-Formulas נוצר על ידי ה-PyInstaller בגיטהאב
Source: "dist\Talmudic-Formulas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. קבצי עזר נוספים
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; יצירת קיצור דרך בתפריט התחלה - וודא ששם ה-EXE תואם למה שמוגדר ב-PyInstaller
Name: "{group}\Talmudic Formulas"; Filename: "{app}\Talmudic-Formulas.exe"
; יצירת קיצור דרך על שולחן העבודה
Name: "{commondesktop}\Talmudic Formulas"; Filename: "{app}\Talmudic-Formulas.exe"; Tasks: desktopicon

[Run]
; אפשרות להריץ את התוכנה מיד בסיום ההתקנה
Filename: "{app}\Talmudic-Formulas.exe"; Description: "{cm:LaunchProgram,Talmudic Formulas}"; Flags: nowait postinstall skipifsilent

[Code]
// קוד זה נועד לוודא שהגרסה מתעדכנת אוטומטית דרך ה-GitHub Actions
// אין צורך לשנות כאן כלום