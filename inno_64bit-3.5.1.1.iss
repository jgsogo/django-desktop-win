#include <idp.iss>

#define MyAppName "PruebaDjango"
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
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

;[Files]
;Source: "{app}winpython.exe"; DestDir: "{app}"; AfterInstall: RunOtherInstaller

;[Icons]
;Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

;[Run]
;Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


[Tasks]
Name: "install_winpython"; Description: "Install WinPython"; GroupDescription: "WinPython:";

[Run]
Filename: "{app}\winpython.exe"; StatusMsg: "Installing WinPython"; Tasks: install_winpython; Flags: skipifsilent



[UninstallDelete]
Type: files; Name: "{app}\winpython.exe"


[Code]
procedure RunOtherInstaller;
var
  ResultCode: Integer;
begin
  if not Exec(ExpandConstant('{app}\winpython.exe'), '', '', SW_SHOWNORMAL,
    ewWaitUntilTerminated, ResultCode)
  then
    MsgBox('Other installer failed to run!' + #13#10 +
      SysErrorMessage(ResultCode), mbError, MB_OK);
end;

procedure InitializeWizard();
begin
    idpAddFile('http://sourceforge.net/projects/winpython/files/WinPython_3.5/3.5.1.1/WinPython-64bit-3.5.1.1Zero.exe/download', ExpandConstant('{tmp}\winpython.exe'));
    idpDownloadAfter(wpReady);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
    if CurStep = ssPostInstall then 
    begin
        // Copy downloaded files to application directory
        FileCopy(ExpandConstant('{tmp}\winpython.exe'), ExpandConstant('{app}\winpython.exe'), false);
    end;
end;

