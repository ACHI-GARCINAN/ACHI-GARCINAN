#define MyAppName "נוסחאות התלמוד"
#define MyAppExeName "Talmudic-Formulas.exe"
#define MyAppVersion "1.0"

[Setup]
; AppId ייחודי עבור האפליקציה
AppId={{D3B3E5C1-A8F2-4E9D-B6D7-3F1A2C3D4E5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="Achi Garcinan"
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=Talmudic-Formulas-Setup-Win
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; --- הוספת קבצי המידע והרישיון ---
; מציג את תוכן הקובץ כהסכם שחובה לאשר
LicenseFile=license.txt
; מציג את תוכן הקובץ כמידע לפני ההתקנה
InfoBeforeFile=comments.txt

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; לוקח את כל הקבצים ש-PyInstaller יצר בתיקיית ה-installer
Source: "dist-installer\Talmudic-Formulas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; הוספת קבצי הטקסט לתיקיית התוכנה המותקנת (אופציונלי)
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent