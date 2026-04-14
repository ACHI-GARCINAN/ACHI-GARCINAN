[Setup]
AppName=נוסחאות התלמוד
AppVersion=1.0
DefaultDirName={autopf}\Talmud Formulas
DefaultGroupName=נוסחאות התלמוד
OutputDir=Output
OutputBaseFilename=Talmud-Formulas-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
LicenseFile=license.txt
InfoBeforeFile=comments.txt

[Files]
Source: "dist\Talmud-Formulas.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "talmud.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "widgets\*"; DestDir: "{app}\widgets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "JSON_Archive\*.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\נוסחאות התלמוד"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\Talmud-Formulas.exe"; Description: "{cm:LaunchProgram,נוסחאות התלמוד}"; Flags: nowait postinstall skipifsilent