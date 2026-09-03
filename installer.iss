; installer.iss - Inno Setup para Registro E/S (Los Cielos Farm)
; La versión se pasa desde el workflow:  ISCC /DMyAppVersion=1.0.11 installer.iss
; Si no se pasa, usa 0.0.0 como valor por defecto.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#define MyAppName "Registro E-S"
#define MyAppExe "registro_gui.exe"
#define MyAppPublisher "Eduardo A. Fortuny Ruvalcaba"
#define MyAppURL "https://github.com/ALi3naTEd0/entradas_salidas"

[Setup]
; AppId identifica la app para actualizaciones/desinstalación; NO cambiar entre versiones.
AppId={{A7F3C2E1-9B4D-4E6A-8C2F-1D5E7A9B3C4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
; Instalación por-usuario (sin admin) en una carpeta escribible: la app guarda
; registro.csv, backups y config junto al .exe.
DefaultDirName={localappdata}\RegistroES
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=RegistroES-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
