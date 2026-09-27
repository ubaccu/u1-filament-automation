#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef ProjectRoot
  #define ProjectRoot "..\.."
#endif
#ifndef BuildRoot
  #define BuildRoot "..\..\build\windows"
#endif

[Setup]
AppId={{8B9F4D60-E0FA-4DB4-93E1-B813AC2A3346}
AppName=U1 Filament Automation
AppVersion={#MyAppVersion}
AppPublisher=Bottega3DLab
AppPublisherURL=https://github.com/ubaccu/u1-filament-automation
DefaultDirName={localappdata}\Programs\U1 Filament Automation
DefaultGroupName=U1 Filament Automation
DisableProgramGroupPage=yes
LicenseFile={#ProjectRoot}\LICENSE
OutputDir={#ProjectRoot}\dist
OutputBaseFilename=U1-Filament-Automation-v{#MyAppVersion}-Windows-x64-Setup
SetupIconFile={#BuildRoot}\U1FA.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\U1 Filament Automation.exe
CloseApplications=yes

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#ProjectRoot}\dist\U1 Filament Automation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\U1 Filament Automation"; Filename: "{app}\U1 Filament Automation.exe"
Name: "{autodesktop}\U1 Filament Automation"; Filename: "{app}\U1 Filament Automation.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop / Create a desktop shortcut"; GroupDescription: "Collegamenti aggiuntivi / Additional shortcuts:"

[Run]
Filename: "{app}\U1 Filament Automation.exe"; Description: "Avvia U1 Filament Automation / Launch U1 Filament Automation"; Flags: nowait postinstall skipifsilent
