[Setup]
AppName=נוסחאות התלמוד
; הגרסה תתעדכן אוטומטית מה-YAML
AppVersion=1.8
DefaultDirName={userdesktop}\נוסחאות התלמוד
DefaultGroupName=נוסחאות התלמוד
OutputDir=Output
OutputBaseFilename=Talmud-Formulas-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
ShowLanguageDialog=yes

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[Files]
Source: "dist\Talmud-Formulas.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "talmud.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "widgets\*"; DestDir: "{app}\widgets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\Talmud-Formulas.exe"; Description: "הפעל את נוסחאות התלמוד"; Flags: nowait postinstall skipifsilent