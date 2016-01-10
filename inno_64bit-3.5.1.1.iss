
#include "defines.iss"

#define MyAppVersion "1.5"
#define MyAppPublisher "My Company, Inc."
#define MyAppURL "http://www.example.com/"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{4FA5179E-B8C4-4398-AB75-538FD677B3BF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename={#MyAppName}_py{#PythonVersion}_{#architecture}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#DeployDir}/*"; DestDir: "{app}/bin"; Flags: ignoreversion recursesubdirs createallsubdirs; Permissions: users-modify
Source: "{#DjangoDir}/*"; Excludes: "*.~*,*.pyc,*.sqlite3"; DestDir: "{app}/{#MyAppName}"; Components: {#MyAppName}; Flags: ignoreversion recursesubdirs createallsubdirs; Permissions: users-modify
Source: "./deploy/requirements.txt"; DestDir: "{app}/tmp"; Components: {#MyAppName}; Flags: ignoreversion
Source: "./deploy/run.py"; DestDir: "{app}/{#MyAppName}/{#ManagePyRelPath}"; Components: {#MyAppName}; Flags: ignoreversion
Source: "./cef/cefsimple/res/development.ico"; DestDir: "{app}/bin"
Source: "{#WinPythonBasename}/*"; Excludes: "*.~*,*.pyc"; DestDir: "{app}/{#WinPythonBasename}"; Components: {#MyAppName}; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}/{#MyAppName}"; Permissions: everyone-full

[Components]
Name: "winpython"; Description: "WinPython {#PythonVersion} {#WinPythonArchitecture}"; Types: full compact custom; Flags: fixed
Name: "{#MyAppName}"; Description: "Django application: {#MyAppName}"; Types: full

[Run]
Filename: {app}\bin\cefsimple.exe; Description: "Start {#MyAppName} after finishing installation"; WorkingDir: "{app}"; Parameters: "--python=""{app}\{#WinPythonRelExe}"" --manage=""{app}\{#MyAppName}\{#ManagePyRelPath}\run.py"" --url={#Home}"; Flags: postinstall skipifsilent

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\bin\cefsimple.exe"; WorkingDir: "{app}"; Parameters: "--python=""{app}\{#WinPythonRelExe}"" --manage=""{app}\{#MyAppName}\{#ManagePyRelPath}\run.py"" --url={#Home}"; IconFilename: "{app}/bin/development.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\bin\cefsimple.exe"; WorkingDir: "{app}"; Parameters: "--python=""{app}\{#WinPythonRelExe}"" --manage=""{app}\{#MyAppName}\{#ManagePyRelPath}\run.py"" --url={#Home}"; IconFilename: "{app}/bin/development.ico"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
    if CurStep = ssPostInstall then 
    begin          
        // Apply migrations
        WizardForm.StatusLabel.Caption := 'Applying migrations to project...';
        if not Exec(ExpandConstant('{app}\{#WinPythonRelExe}'), ExpandConstant('"{app}\{#MyAppName}\{#ManagePyPath}" migrate'), '' , SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)
        then
            MsgBox('Other installer failed to run!' + #13#10 + SysErrorMessage(ResultCode), mbError, MB_OK);
           
        // Create superuser (if not already installed)
        if not RegKeyExists(HKLM, ExpandConstant('Software\{#MyAppPublisher}\{#MyAppName}')) then
        begin
            WizardForm.StatusLabel.Caption := 'Create superuser to access admin...';
            if not Exec(ExpandConstant('{app}\{#WinPythonRelExe}'), ExpandConstant('"{app}\{#MyAppName}\{#ManagePyPath}" createsuperuser'), '' , SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)
            then
                MsgBox('Other installer failed to run!' + #13#10 + SysErrorMessage(ResultCode), mbError, MB_OK);
                
            RegWriteStringValue(HKLM, ExpandConstant('Software\{#MyAppPublisher}\{#MyAppName}'), 'DB', ExpandConstant('{sysuserinfoname}'));
        end;
    end;
end;


procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegKeyExists(HKLM, ExpandConstant('Software\{#MyAppPublisher}\{#MyAppName}')) then
        RegDeleteKeyIncludingSubkeys(HKLM, ExpandConstant('Software\{#MyAppPublisher}\{#MyAppName}'));
  end;
end;
