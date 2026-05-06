[Setup]
#define MyAppName "נוסחאות התלמוד"
#define MyAppExeName "TalmudicFormulas.exe"
#define MyAppVersion "1.0"
#define MyAppId "{{D3B3E5C1-A8F2-4E9D-B6D7-3F1A2C3D4E5F}"

; AppId ייחודי עבור האפליקציה
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="Achi Garcinan"
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=TalmudicFormulas-Setup-Win
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; לוקח את כל הקבצים ש-PyInstaller יצר בתיקיית ה-installer (שימוש בשם המדויק מה-YAML)
Source: "dist-installer\TalmudicFormulas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; הוספת קבצי טקסט לתיקיית התוכנה המותקנת
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion
; הוספת בסיס הנתונים (חשוב מאוד אם הוא לא בתוך התיקייה ש-PyInstaller אסף)
Source: "talmud.db"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent