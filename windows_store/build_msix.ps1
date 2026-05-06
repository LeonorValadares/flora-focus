$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root "venv\Scripts\python.exe"
$exeRoot = Join-Path $root "windows_store\dist\FloraFocus"
$msixRoot = Join-Path $root "windows_store\msix"
$packageRoot = Join-Path $msixRoot "package"
$assetsRoot = Join-Path $msixRoot "Assets"
$outputMsix = Join-Path $msixRoot "FloraFocus_1.0.0.0_x64.msix"
$publisher = "CN=FloraFocusTest"
$packageName = "LeonorValadares.FloraFocus"
$displayName = "Flora Focus"
$description = "Flora Focus packaged as a local MSIX test build."

$sdkBin = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x64"
$makeAppx = Join-Path $sdkBin "makeappx.exe"
$makePri = Join-Path $sdkBin "makepri.exe"
$signTool = Join-Path $sdkBin "signtool.exe"

foreach ($tool in @($python, $makeAppx, $makePri, $signTool)) {
    if (-not (Test-Path -LiteralPath $tool)) {
        throw "Missing required tool: $tool"
    }
}

if (-not (Test-Path -LiteralPath $exeRoot)) {
    throw "Missing packaged executable folder: $exeRoot"
}

Remove-Item -LiteralPath $packageRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $packageRoot | Out-Null

Get-ChildItem -LiteralPath $exeRoot -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $packageRoot -Recurse -Force
}

& $python (Join-Path $PSScriptRoot "generate_msix_assets.py")
Copy-Item -LiteralPath $assetsRoot -Destination $packageRoot -Recurse -Force

$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:uap10="http://schemas.microsoft.com/appx/manifest/uap/windows10/10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap uap10 rescap">
  <Identity Name="$packageName" Version="1.0.0.0" Publisher="$publisher" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>$displayName</DisplayName>
    <PublisherDisplayName>Flora Focus</PublisherDisplayName>
    <Description>$description</Description>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Resources>
    <Resource Language="en-us" />
  </Resources>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.26200.0" />
  </Dependencies>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  <Applications>
    <Application Id="FloraFocus" Executable="FloraFocus.exe" EntryPoint="Windows.FullTrustApplication" uap10:RuntimeBehavior="packagedClassicApp" uap10:TrustLevel="mediumIL">
      <uap:VisualElements
        DisplayName="$displayName"
        Description="$description"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" Square310x310Logo="Assets\Square310x310Logo.png" />
        <uap:SplashScreen Image="Assets\SplashScreen.png" BackgroundColor="#112F5E" />
      </uap:VisualElements>
    </Application>
  </Applications>
</Package>
"@

$manifestPath = Join-Path $packageRoot "AppxManifest.xml"
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8

Push-Location $packageRoot
try {
    & $makePri createconfig /cf priconfig.xml /dq en-US | Out-Null
    & $makePri new /pr $packageRoot /cf (Join-Path $packageRoot "priconfig.xml") | Out-Null
}
finally {
    Pop-Location
}

if (Test-Path -LiteralPath $outputMsix) {
    Remove-Item -LiteralPath $outputMsix -Force
}
& $makeAppx pack /d $packageRoot /p $outputMsix /o

$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $publisher } | Select-Object -First 1
if (-not $cert) {
    $cert = New-SelfSignedCertificate `
        -Type Custom `
        -Subject $publisher `
        -KeyUsage DigitalSignature `
        -FriendlyName "Flora Focus Local MSIX" `
        -CertStoreLocation "Cert:\CurrentUser\My"
}

$cerPath = Join-Path $msixRoot "FloraFocusTest.cer"
Export-Certificate -Cert ("Cert:\CurrentUser\My\" + $cert.Thumbprint) -FilePath $cerPath -Force | Out-Null

foreach ($storePath in @("Cert:\CurrentUser\TrustedPeople", "Cert:\CurrentUser\Root")) {
    if (-not (Get-ChildItem $storePath | Where-Object { $_.Thumbprint -eq $cert.Thumbprint })) {
        Import-Certificate -FilePath $cerPath -CertStoreLocation $storePath | Out-Null
    }
}

& $signTool sign /fd SHA256 /sha1 $cert.Thumbprint /s My $outputMsix

Get-Item $outputMsix | Select-Object FullName, Length, LastWriteTime
