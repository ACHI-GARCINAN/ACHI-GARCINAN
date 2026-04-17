[Setup]
; הגדרות בסיסיות של התוכנה
AppName=נוסחאות התלמוד
AppVersion=1.1
DefaultDirName={autopf}\Talmud Formulas
DefaultGroupName=נוסחאות התלמוד
OutputDir=Output
OutputBaseFilename=Talmud-Formulas-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes

; חלוניות אישור ומידע (דורש שקבצי הטקסט יהיו קיימים בתיקייה)
LicenseFile=license.txt
InfoBeforeFile=comments.txt

; הגדרות שפה - מאפשר למשתמש לבחור שפה בעת ההפעלה
ShowLanguageDialog=yes

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; הקובץ הראשי - שים לב: הוא כבר כולל את ה-DB בפנים בזכות ה-PyInstaller
Source: "dist\Talmud-Formulas.exe"; DestDir: "{app}"; Flags: ignoreversion

; תיקיית הווידג'טים
Source: "widgets\*"; DestDir: "{app}\widgets"; Flags: ignoreversion recursesubdirs createallsubdirs

; קבצי עזר נוספים
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; יצירת קיצורי דרך
Name: "{group}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"

[Run]
; הרצת התוכנה בסיום ההתקנה
Filename: "{app}\Talmud-Formulas.exe"; Description: "{cm:LaunchProgram,נוסחאות התלמוד}"; Flags: nowait postinstall skipifsilent