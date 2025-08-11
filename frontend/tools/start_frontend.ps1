$ErrorActionPreference = 'SilentlyContinue'

$root = Split-Path -Parent $PSScriptRoot
$fe = $root
Set-Location $fe
if (-not (Test-Path 'logs')) { New-Item -ItemType Directory -Path 'logs' | Out-Null }
$logFile = Join-Path (Get-Location) 'logs\frontend.log'
if (Test-Path $logFile) { Move-Item -Force $logFile ("{0}.{1:yyyyMMdd_HHmmss}.log" -f $logFile, (Get-Date)) }

$env:NODE_OPTIONS = ''
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:BROWSER = 'none'
$port = 3004

$cmd = 'npx'
$args = @('next','dev','-p',"$port")
Start-Process -FilePath $cmd -ArgumentList $args -WorkingDirectory $fe -RedirectStandardOutput $logFile -RedirectStandardError $logFile -WindowStyle Hidden | Out-Null
Write-Output ('Started frontend process. Logs: {0}' -f $logFile)

$ready = $false
for ($i=0; $i -lt 60; $i++) {
  try {
    Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:" + $port) -TimeoutSec 2 | Out-Null
    Write-Output ("http://localhost:" + $port)
    $ready = $true
    break
  } catch {}
  Start-Sleep -Seconds 1
}
if (-not $ready) { Write-Output 'Frontend not ready yet' }
