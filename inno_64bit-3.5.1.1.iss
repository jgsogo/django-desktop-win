#include <idp.iss>
#include <defines.iss>

#define MyAppVersion "1.5"
#define MyAppPublisher "My Company, Inc."
#define MyAppURL "http://www.example.com/"
#define MyAppExeName "start_all.bat"

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
Source: "{#DjangoDir}/*"; DestDir: "{app}/{#MyAppName}"; Components: {#MyAppName}

[Components]
Name: "winpython"; Description: "WinPython {#PythonVersion} {#WinPythonArchitecture}"; Types: full compact custom; Flags: fixed
Name: "django_app"; Description: "Django application: {#MyAppName}"; Types: full

[UninstallDelete]
Type: files; Name: "{app}\{#WinPythonFullName}.exe"
Type: filesandordirs; Name: "{app}\{#WinPythonFullName}"


[Code]
procedure InitializeWizard();
begin
    idpAddFile('{#WinPythonDownload}', ExpandConstant('{tmp}\{#WinPythonFullName}.exe'));
    
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
        FileCopy(ExpandConstant('{tmp}\{#WinPythonFullName}.exe'), ExpandConstant('{app}\{#WinPythonFullName}.exe'), false);
        if not Exec(ExpandConstant('{app}\{#WinPythonFullName}.exe'), ExpandConstant('/S /D="{app}\{#WinPythonFullName}\"'), '' , SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)
        then
            MsgBox('Other installer failed to run!' + #13#10 + SysErrorMessage(ResultCode), mbError, MB_OK);
    end;
end;

