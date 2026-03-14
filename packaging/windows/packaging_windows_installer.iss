; Inno Setup script for UDPLogViewer
; Place this file in: packaging/windows/installer.iss (recommended)
; Requires Inno Setup 6.x

#define AppName "UDPLogViewer"
#define AppExe "UDPLogViewer.exe"
#define AppPublisher "Bernhard Klein"
#define AppURL "https://github.com/<your-username>/udp-log-viewer"
#define AppSupportURL "https://github.com/<your-username>/udp-log-viewer/issues"

; Version: keep in sync with your freeze_setup_win.py / pyproject.toml tag/release
#define AppVersion "0.14.0"

; Relative path to cx_Freeze output folder (resolved by build script)
; Example produced by cx_Freeze:
;   build\exe.win-amd64-3.12\
#define BuildDir "build\exe.win-amd64-3.12"

; Optional: provide an icon
#define AppIcon "packaging\windows\app.ico"

[Setup]
AppId={{A9B8F8D8-3B36-4B0A-9F8C-UDPLOGVIEWER-0001}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppSupportURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; Use icon if present (optional)
SetupIconFile={#AppIcon}

; Uncomment once you have a license file
; LicenseFile=LICENSE

; Modern Windows
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy everything from the cx_Freeze build directory into the install dir
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon; WorkingDir: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
