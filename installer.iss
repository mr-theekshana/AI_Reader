; AI Reader - Professional Windows Installer Script
; Port of Inno Setup 6.x

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=AI Reader
AppVersion=3.0
AppVerName=AI Reader v3.0
AppPublisher=AI Reader
DefaultDirName={autopf}\AI Reader
DefaultGroupName=AI Reader
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=AI_Reader_Setup_v3.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\AI Reader.exe
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Note: 'checked' is the default behavior in Inno Setup. 
; No Flags needed to have it checked by default.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\AI Reader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AI Reader"; Filename: "{app}\AI Reader.exe"
Name: "{group}\Uninstall AI Reader"; Filename: "{uninstallexe}"
Name: "{autodesktop}\AI Reader"; Filename: "{app}\AI Reader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AI Reader.exe"; Description: "Launch AI Reader"; Flags: nowait postinstall skipifsilent