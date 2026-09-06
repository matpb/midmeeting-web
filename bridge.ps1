# Installs midmeeting-bridge. irm https://midmeeting.com/bridge.ps1 | iex
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$version = "v1.1.0"
$asset = "midmeeting-bridge-windows-x86_64.exe"
$url = "https://github.com/matpb/midmeeting-web/releases/download/$version/$asset"

$binDir = Join-Path $env:LOCALAPPDATA "midmeeting\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$dest = Join-Path $binDir "midmeeting-bridge.exe"

Write-Host "Downloading $asset..."
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $dest

# status exits 1 when the bridge is off; a launch failure throws instead.
try {
    & $dest status | Out-Null
} catch {
    Write-Error "Downloaded binary at $dest did not run. Check the download and try again."
    exit 1
}
Write-Host "Installed to $dest"

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathEntries = $userPath -split ";"
if ($pathEntries -notcontains $binDir) {
    $newPath = if ($userPath) { "$userPath;$binDir" } else { $binDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $binDir to your user PATH. Open a new terminal for it to take effect."
} else {
    Write-Host "$binDir is already on your user PATH."
}
