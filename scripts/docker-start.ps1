<#
.SYNOPSIS
    Start Docker Desktop on this machine, working around the stale analytics socket.

.DESCRIPTION
    Docker Desktop 4.37.1 leaves a stale Linux socket behind in
    %LOCALAPPDATA%\Docker\run. On the next start the backend tries to remove
    it, fails with "The file cannot be accessed by the system", and aborts -
    which then triggers a factory reset that wipes the docker-desktop distro.

    The socket cannot be deleted from Windows (error 1920: the filesystem does
    not recognise it), but it can be removed from the WSL side. This script
    does that first, then starts Docker Desktop and waits for the engine.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/docker-start.ps1
#>
$ErrorActionPreference = 'Stop'

$socketWin = Join-Path $env:LOCALAPPDATA 'Docker\run\userAnalyticsOtlpHttp.sock'
$drive = $socketWin.Substring(0, 1).ToLower()
$rest = $socketWin.Substring(2) -replace '\\', '/'
$socketWsl = "/mnt/$drive$rest"

$engine = docker version --format '{{.Server.Version}}' 2>$null
if ($engine) {
    Write-Host "Docker engine already running ($engine)."
    exit 0
}

Write-Host "Removing stale socket: $socketWsl"
wsl --system -- /bin/rm -f $socketWsl 2>$null | Out-Null

Write-Host 'Starting Docker Desktop...'
Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden

for ($i = 0; $i -lt 36; $i++) {
    Start-Sleep -Seconds 5
    $engine = docker version --format '{{.Server.Version}}' 2>$null
    if ($engine) {
        Write-Host "Docker engine up: $engine"
        exit 0
    }
}

Write-Error 'Docker engine did not come up within 3 minutes.'
exit 1
