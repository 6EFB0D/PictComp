; PictComp Inno Setup スクリプト
; Inno Setup 6.x 用

#define MyAppName "PictComp"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Office Go Plan"
#define MyAppURL "https://github.com/6EFB0D/PictComp"
#define MyAppExeName "PictComp.exe"

[Setup]
; アプリケーション情報
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/discussions
AppUpdatesURL={#MyAppURL}/releases

; インストール先
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=no

; 出力設定
OutputDir=..\installer_output
OutputBaseFilename=PictComp-{#MyAppVersion}-setup
SetupIconFile=..\assets\icon\pictcomp_bright.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; 圧縮設定
Compression=lzma2
SolidCompression=yes

; 権限
PrivilegesRequired=admin

; Windows バージョン
MinVersion=10.0

; UI設定
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; GUI版
Source: "..\dist\PictComp.exe"; DestDir: "{app}"; Flags: ignoreversion

; アイコン
Source: "..\assets\icon\pictcomp_bright.ico"; DestDir: "{app}\assets\icon"; Flags: ignoreversion

; ライセンス
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; README（スタートメニューにも配置）
Source: "..\README_RELEASE.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion

[Icons]
; スタートメニュー
Name: "{group}\PictComp"; Filename: "{app}\PictComp.exe"; IconFilename: "{app}\assets\icon\pictcomp_bright.ico"
Name: "{group}\README"; Filename: "{app}\README.md"; IconFilename: "{sys}\shell32.dll"; IconIndex: 1
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; デスクトップ
Name: "{autodesktop}\PictComp"; Filename: "{app}\PictComp.exe"; IconFilename: "{app}\assets\icon\pictcomp_bright.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
