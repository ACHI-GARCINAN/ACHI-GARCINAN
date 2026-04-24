#define MyAppName "נוסחאות התלמוד"
#define MyAppExeName "Talmudic-Formulas.exe"

[Setup]
AppId={{D3B3E5C1-A8F2-4E9D-B6D7-3F1A2C3D4E5F}
AppName={#MyAppName}
AppVersion=1.10
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

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; השורה הבאה תתעדכן אוטומטית על ידי ה-YAML לתיקיית dist-installer
Source: "dist\Talmudic-Formulas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent