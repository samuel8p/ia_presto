# start-all.ps1 - levanta los microservicios de Presto (auth, transactions, chat, gateway)
#
# Uso:
#   .\start-all.ps1              -> levanta lo que falte (omite lo que ya corre)
#   .\start-all.ps1 -Restart     -> frena todo y vuelve a levantar
#
# Si Windows bloquea el script por la politica de ejecucion:
#   powershell -ExecutionPolicy Bypass -File .\start-all.ps1

[CmdletBinding()]
param(
  [switch]$Restart
)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_services.ps1')

Write-Host ''
Write-Host 'Presto - start-all' -ForegroundColor Cyan
Write-Host '------------------' -ForegroundColor DarkGray

if ($Restart) {
  Write-Host 'Reiniciando: freno todo primero...' -ForegroundColor Yellow
  Stop-AllServices
  Start-Sleep -Seconds 2
}

$logDir = Join-Path $IARoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

foreach ($svc in $Services) {
  if (Test-ServicePort -Port $svc.Port) {
    Write-Host ("  [=] {0,-12} :{1} ya estaba corriendo (se omite)" -f $svc.Name, $svc.Port) -ForegroundColor DarkYellow
    continue
  }

  if (-not (Test-Path $svc.Python)) {
    Write-Host ("  [!] {0,-12} falta el ejecutable de python: {1}" -f $svc.Name, $svc.Python) -ForegroundColor Red
    Write-Host ("      revisa que exista el venv en {0}" -f $svc.Dir) -ForegroundColor DarkGray
    continue
  }

  $outLog = Join-Path $logDir ($svc.Name + '.out.log')
  $errLog = Join-Path $logDir ($svc.Name + '.err.log')

  Start-Process -FilePath $svc.Python `
    -ArgumentList $svc.Script `
    -WorkingDirectory $svc.Dir `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden | Out-Null

  Write-Host ("  [+] {0,-12} :{1} iniciando..." -f $svc.Name, $svc.Port) -ForegroundColor Cyan
  Start-Sleep -Milliseconds 700
}

Start-Sleep -Seconds 3
Show-ServiceStatus

Write-Host ''
Write-Host ("Logs:  {0}" -f $logDir) -ForegroundColor DarkGray
Write-Host 'Health: http://127.0.0.1:8080/api/health' -ForegroundColor DarkGray
Write-Host ''
