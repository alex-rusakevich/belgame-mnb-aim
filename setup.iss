[Setup]
AppId=belgame_mnb_aim
AppName=Беларусіфікатар для гульні "Mount & Blade. Агнём і мячом. Вялікія бітвы"
AppVersion=1.0
DefaultDirName={pf}
UsePreviousAppDir=yes
AppendDefaultDirName=no
DisableDirPage=auto
OutputBaseFilename=Беларусіфікатар_Mount_&_Blade_Агнём_і_мячом
DirExistsWarning=no

[Languages]
Name: "be"; MessagesFile: "Belarusian.isl"

[Files]
Source: "translation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "language.txt"; DestDir: "{userdocs}\Mount&Blade With Fire and Sword"; Flags: ignoreversion recursesubdirs

[Run]
Filename: "{app}\mb_wfas.exe"; Description: "Запусціць гульню"; Flags: postinstall nowait skipifsilent unchecked