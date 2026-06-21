[Setup]
; MyAppVersion מועבר דינמית מה-GitHub Actions באמצעות /DMyAppVersion="..."
; אל תגדיר כאן #define MyAppVersion — זה ידרוס את הערך הדינמי!
#define MyAppName "נוסחאות התלמוד"
#define MyAppExeName "TalmudicFormulas.exe"
#define MyAppId "{{D3B3E5C1-A8F2-4E9D-B6D7-3F1A2C3D4E5F}"

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
LicenseFile=Usage Note.txt
InfoAfterFile=comments.txt

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; כל הקבצים שיצר PyInstaller בתיקיית dist-installer
Source: "dist-installer\TalmudicFormulas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; קבצי טקסט — עם skipifsourcedoesntexist כדי שהבנייה לא תיכשל אם חסרים
Source: "Usage Note.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; בסיס הנתונים — כבר נכלל ב-PyInstaller, אבל נוסף גם כאן לוודאות
Source: "talmud.db"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
