[Setup]
AppName=נוסחאות התלמוד
AppVersion=1.3
DefaultDirName={autopf}\Talmud Formulas
DefaultGroupName=נוסחאות התלמוד
OutputDir=Output
OutputBaseFilename=Talmud-Formulas-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
LicenseFile=license.txt
InfoBeforeFile=comments.txt
; מאפשר למשתמש לבחור שפה בעת פתיחת ההתקנה
ShowLanguageDialog=yes

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; הקובץ הראשי שנוצר בתיקיית dist
Source: "dist\Talmud-Formulas.exe"; DestDir: "{app}"; Flags: ignoreversion
; מסד הנתונים - קריטי שיהיה באותה תיקייה של ה-EXE
Source: "talmud.db"; DestDir: "{app}"; Flags: ignoreversion
; תיקיית הווידג'טים וכל תוכנה
Source: "widgets\*"; DestDir: "{app}\widgets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\Talmud-Formulas.exe"; Description: "{cm:LaunchProgram,נוסחאות התלמוד}"; Flags: nowait postinstall skipifsilent