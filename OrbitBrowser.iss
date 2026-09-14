#define MyAppName "Orbit Browser"
#define MyAppVersion "1.16.17"
#define MyAppPublisher "Orbit Browsers"
#define MyAppExeName "OrbitBrowser.exe"
#define MyAppInstallDir "{autopf}\OrbitBrowsers"

[Setup]
AppId={{9D6B8C5F-9B9E-4D48-92D4-1B8518505A5B}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={#MyAppInstallDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
OutputDir=installer
OutputBaseFilename=OrbitBrowser-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupIconFile=assets\orbit_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no

[Messages]
WelcomeLabel1=Добро пожаловать в Orbit Browser!
WelcomeLabel2=Установка Orbit Browser {#MyAppVersion} на компьютер.
FinishedLabel=Установка Orbit Browser завершена.

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

[Files]
Source: "build_out\OrbitBrowser.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Orbit Browser"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Orbit Browser"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"

[Dirs]
Name: "{localappdata}\OrbitBrowser"
Name: "{localappdata}\OrbitBrowser\config"
Name: "{localappdata}\OrbitBrowser\profiles"
Name: "{localappdata}\OrbitBrowser\workspaces"
Name: "{localappdata}\OrbitBrowser\themes"
Name: "{localappdata}\OrbitBrowser\notes"
Name: "{localappdata}\OrbitBrowser\downloads"
Name: "{localappdata}\OrbitBrowser\cache"
Name: "{localappdata}\OrbitBrowser\logs"
Name: "{localappdata}\OrbitBrowser\backups"
Name: "{localappdata}\OrbitBrowser\data"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить Orbit Browser"; Flags: nowait postinstall skipifsilent
