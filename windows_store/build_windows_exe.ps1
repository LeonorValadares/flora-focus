$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root "venv\Scripts\python.exe"
$icon = Join-Path $root "FloraFocus.ico"
$fallbackIcon = Join-Path $root "dist\Flora Focus Portable\FloraFocus.ico"
$distPath = Join-Path $root "windows_store\dist"
$workPath = Join-Path $root "windows_store\build"
$specPath = Join-Path $root "windows_store"
$entry = Join-Path $root "kivy_app\main.py"
$asset = Join-Path $root "FloraFocus.png"

if (-not (Test-Path -LiteralPath $icon) -and (Test-Path -LiteralPath $fallbackIcon)) {
    Copy-Item -LiteralPath $fallbackIcon -Destination $icon -Force
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing build Python: $python"
}

if (-not (Test-Path -LiteralPath $icon)) {
    throw "Missing icon file: $icon"
}

if (-not (Test-Path -LiteralPath $asset)) {
    throw "Missing asset file: $asset"
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name FloraFocus `
    --icon $icon `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $specPath `
    --add-data "$asset;." `
    $entry
