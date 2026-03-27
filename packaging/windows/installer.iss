; Inno Setup script for UDPLogViewer
; Requires Inno Setup 6.x

#ifndef AppName
  #define AppName "UDPLogViewer"
#endif

#ifndef AppExe
  #define AppExe "UDPLogViewer.exe"
#endif

#ifndef AppPublisher
  #define AppPublisher "Bernhard Klein"
#endif

#ifndef AppURL
  #define AppURL "https://github.com/<your-username>/udp-log-viewer"
#endif

#ifndef AppSupportURL
  #define AppSupportURL "https://github.com/<your-username>/udp-log-viewer/issues"
#endif

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#ifndef BuildDir
  #define BuildDir "build\exe.win-amd64-3.12"
#endif

#ifndef AppIcon
  #define AppIcon "packaging\windows\app.ico"
#endif

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
SetupIconFile={#AppIcon}
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy everything from the cx_Freeze output directory into the install dir.
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon; WorkingDir: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
