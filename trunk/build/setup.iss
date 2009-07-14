#define MyAppName "Ramses"
#define MyAppVer "1.0.0"
#define MyAppVerName "Ramses 1.0.0"
#define MyAppPublisher "By Gabe Rudy"
#define MyAppURL "http://code.google.com/p/ramses-build/"
#define MyAppExeName "ramses.exe"
#define MyPlatform "Win32"
#define MyOutputDir "D:/Development/Build/ramses/InstallerWin32"
#define MyStageDir "D:/Development/Build/ramses/StageWin32/dist/ramses"
#define MyScriptWriterPath "D:/Development/Build/ramses/SourceWin32/build/write-launch-script.js"
#define MySetupIconPath "D:/Development/Build/ramses/SourceWin32/build/install.ico"
; NOTE: The above lines are for static testing of this Inno Setup script.
; The build process replaces these lines of the script with
; build-specific information to "just-work" on your build setup.

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{A67C78BD-182C-4C53-B47E-30FD84889D9E}
AppName={#MyAppName}
AppVerName={#MyAppVerName} {#MyPlatform}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}\
AllowNoIcons=true
OutputDir={#MyOutputDir}
OutputBaseFilename={#MyAppName}-{#MyPlatform}-{#MyAppVer}
SetupIconFile={#MySetupIconPath}
Compression=lzma
SolidCompression=true
UninstallDisplayIcon={app}\{#MyAppName}.exe
UninstallDisplayName={#MyAppName} {#MyPlatform}

VersionInfoDescription={#MyAppName}-{#MyPlatform}-{#MyAppVer}
VersionInfoTextVersion={#MyAppName}-{#MyPlatform}-{#MyAppVer}
VersionInfoCompany={#MyAppPublisher}
RestartIfNeededByRun=false

[Languages]
Name: english; MessagesFile: compiler:Default.isl

[Tasks]
Name: systempath; Description: Append {#MyAppName} to the System PATH Environment Variable; GroupDescription: Environment Variables:
Name: userpath; Description: Append {#MyAppName} to the User' PATH Environment Variable; GroupDescription: Environment Variables:; Flags: unchecked

[Files]
Source: {#MyStageDir}\*; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs
Source: {#MyScriptWriterPath}; DestDir: {tmp}; Flags: deleteafterinstall
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: {group}\{#MyAppName} Command Prompt; Filename: {app}\{#MyAppName}CommandPrompt.bat; WorkingDir: {app}; IconFilename: {app}\{#MyAppExeName}
Name: {group}\{cm:ProgramOnTheWeb,{#MyAppName}}; Filename: {#MyAppURL}
Name: {group}\{cm:UninstallProgram,{#MyAppName}}; Filename: {uninstallexe}

[Run]
Filename: cscript; Parameters: "{tmp}\write-launch-script.js {#MyAppName}  ""{app}"""; WorkingDir: {app}; StatusMsg: Creating a launch script for a {#MyAppName} configured command prompt

[Registry]
Root: HKLM; Subkey: SYSTEM\CurrentControlSet\Control\Session Manager\Environment; ValueType: expandsz; ValueName: Path; ValueData: "{olddata};{app}"; Tasks: systempath
Root: HKCU; Subkey: Environment; ValueType: expandsz; ValueName: Path; ValueData: "{olddata};{app}"; Tasks: userpath

[UninstallDelete]
Name: {app}\*; Type: filesandordirs; Tasks: ; Languages: 
