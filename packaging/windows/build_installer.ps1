$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$BuildRoot = Join-Path $ProjectDir "build\windows"
$PyInstallerWork = Join-Path $ProjectDir "build\pyinstaller-windows"
$DistDir = Join-Path $ProjectDir "dist"
$AppName = "U1 Filament Automation"
$Version = (& python -c "import sys; sys.path.insert(0, r'$ProjectDir\src'); from u1_filament_automation import __version__; print(__version__)").Trim()

if ($Version -notmatch '^[0-9A-Za-z.]+$') {
    throw "Versione non valida: $Version"
}

$AppDist = Join-Path $DistDir $AppName
foreach ($Target in @($BuildRoot, $PyInstallerWork, $AppDist)) {
    if (Test-Path $Target) {
        Remove-Item -Recurse -Force $Target
    }
}
New-Item -ItemType Directory -Force -Path $BuildRoot, $DistDir | Out-Null

$SourceIcon = Join-Path $ProjectDir "src\u1_filament_automation\assets\u1fa_logo.png"
$IconFile = Join-Path $BuildRoot "U1FA.ico"
& python -c "from PIL import Image; image=Image.open(r'$SourceIcon').convert('RGBA'); image.save(r'$IconFile', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if ($LASTEXITCODE -ne 0) { throw "Creazione icona Windows fallita" }

$AssetsDir = Join-Path $ProjectDir "src\u1_filament_automation\assets"
$DataDestination = "u1_filament_automation\assets"
$DataFiles = @(
    "u1fa_logo.png",
    "flow_calibrator_stock.py",
    "flow_calibrator_v6.py",
    "adaptive_pa_macro.cfg"
)
$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm", "--clean", "--windowed", "--onedir",
    "--name", $AppName,
    "--icon", $IconFile,
    "--collect-data", "certifi",
    "--workpath", $PyInstallerWork,
    "--specpath", $BuildRoot,
    "--distpath", $DistDir
)
foreach ($File in $DataFiles) {
    $PyInstallerArgs += @("--add-data", "$(Join-Path $AssetsDir $File);$DataDestination")
}
$PyInstallerArgs += (Join-Path $ScriptDir "u1fa_bootstrap.py")
& python @PyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw "Build PyInstaller Windows fallita" }

$FrozenExe = Join-Path $AppDist "$AppName.exe"
$SelfTestEnvironment = @{ U1FA_DESKTOP_SELFTEST = "1" }
$SelfTest = Start-Process -FilePath $FrozenExe -Wait -PassThru -Environment $SelfTestEnvironment
if ($SelfTest.ExitCode -ne 0) {
    throw "Self-test applicazione Windows fallito con codice $($SelfTest.ExitCode)"
}

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Iscc) {
    throw "Inno Setup 6 non trovato. Installarlo prima di eseguire questo script."
}

$IssFile = Join-Path $ScriptDir "U1FA.iss"
& $Iscc "/DMyAppVersion=$Version" "/DProjectRoot=$ProjectDir" "/DBuildRoot=$BuildRoot" $IssFile
if ($LASTEXITCODE -ne 0) { throw "Creazione installer Windows fallita" }

$Installer = Join-Path $DistDir "U1-Filament-Automation-v$Version-Windows-x64-Setup.exe"
if (-not (Test-Path $Installer)) { throw "Installer Windows non trovato: $Installer" }
Get-FileHash -Algorithm SHA256 $Installer | Format-List
Write-Host "Installer creato: $Installer"
