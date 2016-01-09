#include <idp.iss>
#include "defines.iss"

#define MyAppVersion "1.5"
#define MyAppPublisher "My Company, Inc."
#define MyAppURL "http://www.example.com/"
#define MyAppExeName "start.bat"

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
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "./deploy/*"; DestDir: "{app}/bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DjangoDir}/*"; DestDir: "{app}/{#MyAppName}"; Components: {#MyAppName}; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "requirements.txt"; DestDir: "{app}/tmp"; Components: {#MyAppName}; Flags: ignoreversion
Source: "run.py"; DestDir: "{app}/{#MyAppName}/{#ManagePyRelPath}"; Components: {#MyAppName}; Flags: ignoreversion

[Components]
Name: "winpython"; Description: "WinPython {#PythonVersion} {#WinPythonArchitecture}"; Types: full compact custom; Flags: fixed
Name: "{#MyAppName}"; Description: "Django application: {#MyAppName}"; Types: full

[UninstallDelete]
Type: files; Name: "{app}\{#WinPythonBasename}.exe"
Type: filesandordirs; Name: "{app}\{#WinPythonBasename}"
Type: filesandordirs; Name: "{app}\start.bat"

[Run]
;Filename: "{app}\{#WinPythonPipRelPath}"; Parameters: "install -r {app}\tmp\requirements.txt"; StatusMsg: "Installing requirements..."
Filename: "{app}\{#WinPythonRelPath}"; Parameters: "{app}\{#MyAppName}\{#ManagePyPath} migrate"; StatusMsg: "Migrate Django database..."



[Code]
procedure InitializeWizard();
begin
    idpAddFile('{#WinPythonDownload}', ExpandConstant('{tmp}\{#WinPythonBasename}.exe'));
    
    idpDownloadAfter(wpReady);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
    if CurStep = ssPostInstall then 
    begin
        // Copy downloaded files to application directory
        WizardForm.StatusLabel.Caption := 'Installing WinPython. Please wait, this can take up to 1 min...';
        FileCopy(ExpandConstant('{tmp}\{#WinPythonBasename}.exe'), ExpandConstant('{app}\{#WinPythonBasename}.exe'), false);
        // Install WinPython
        if not Exec(ExpandConstant('{app}\{#WinPythonBasename}.exe'), ExpandConstant('/S /D="{app}\{#WinPythonBasename}\"'), '' , SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)
        then
            MsgBox('Other installer failed to run!' + #13#10 + SysErrorMessage(ResultCode), mbError, MB_OK);
            
        // Install requirements
        WizardForm.StatusLabel.Caption := 'Installing Python requirements...';
        if not Exec(ExpandConstant('{app}\{#WinPythonBasename}\WinPython Command Prompt.exe'), ExpandConstant('"pip install -r ..\..\tmp\requirements.txt"'), '' , SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)
        then
            MsgBox('Other installer failed to run!' + #13#10 + SysErrorMessage(ResultCode), mbError, MB_OK);
            
        // Create command run script
        SaveStringToFile(ExpandConstant('{app}/start.bat'), #13#10 + ExpandConstant('"{app}/bin/cefsimple.exe" "{app}/{#MyAppName}/{#ManagePyRelPath}/run.py"') + #13#10, False);
    end;
end;

