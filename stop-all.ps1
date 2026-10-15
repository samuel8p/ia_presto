# stop-all.ps1 - frena los microservicios de Presto
#
# Uso:
#   .\stop-all.ps1
#
# Si Windows bloquea el script por la politica de ejecucion:
#   powershell -ExecutionPolicy Bypass -File .\stop-all.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_services.ps1')

Write-Host ''
Write-Host 'Presto - stop-all' -ForegroundColor Cyan
Write-Host '-----------------' -ForegroundColor DarkGray

Stop-AllServices
Show-ServiceStatus
Write-Host ''
