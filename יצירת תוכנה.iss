[Setup]
AppName=Talmud Formulas
AppVersion=1.0
DefaultDirName={autopf}\Talmud Formulas
DefaultGroupName=Talmud Formulas
OutputDir=Output
OutputBaseFilename=Talmud-Formulas-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
LicenseFile=license.txt
InfoBeforeFile=comments.txt

[Files]
Source: "dist\Talmud-Formulas.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "*.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "comments.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Talmud Formulas"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Talmud Formulas"; Filename: "{app}\Talmud-Formulas.exe"; IconFilename: "{app}\icon.ico"