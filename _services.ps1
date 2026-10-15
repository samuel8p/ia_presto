# _services.ps1 - definiciones compartidas para start-all / stop-all
# Presto - microservicios: auth, transactions, chat, gateway
# No se ejecuta solo: lo cargan start-all.ps1 y stop-all.ps1 con dot-sourcing.

$IARoot = $PSScriptRoot

# Tabla de servicios. Un unico lugar para agregar/quitar servicios o cambiar puertos.
$Services = @(
  [pscustomobject]@{
    Name   = 'auth'
    Port   = 5000
    Dir    = (Join-Path $IARoot 'auth\auth-app')
    Python = (Join-Path $IARoot '.venv\Scripts\python.exe')
    Script = 'app.py'
  },
  [pscustomobject]@{
    Name   = 'transactions'
    Port   = 5001
    Dir    = (Join-Path $IARoot 'transactions\transactions-app')
    Python = (Join-Path $IARoot '.venv\Scripts\python.exe')
    Script = 'run.py'
  },
  [pscustomobject]@{
    Name   = 'chat'
    Port   = 5002
    Dir    = (Join-Path $IARoot 'chat\chat-app')
    Python = (Join-Path $IARoot 'chat\chat-app\venv\Scripts\python.exe')
    Script = 'run.py'
  },
  [pscustomobject]@{
    Name   = 'gateway'
    Port   = 8080
    Dir    = (Join-Path $IARoot 'api\api-gateway-app')
    Python = (Join-Path $IARoot 'api\api-gateway-app\venv\Scripts\python.exe')
    Script = 'app.py'
  }
)

# Devuelve los PIDs que estan escuchando en un puerto (ignora PIDs del sistema).
function Get-ListeningPids {
  param([int]$Port)
  $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $conns) { return @() }
  return @(
    $conns |
      Select-Object -ExpandProperty OwningProcess -Unique |
      Where-Object { $_ -and $_ -gt 4 }
  )
}

function Test-ServicePort {
  param([int]$Port)
  $pids = @(Get-ListeningPids -Port $Port)
  return ($pids.Count -gt 0)
}

# Frena todos los servicios. Detecta por puerto y mata el arbol de procesos
# (incluye el lanzador del venv y los hijos del reloader de Flask).
function Stop-AllServices {
  foreach ($svc in $Services) {
    $pids = @(Get-ListeningPids -Port $svc.Port)
    if ($pids.Count -eq 0) {
      Write-Host ("  [ ] {0,-12} :{1} no estaba corriendo" -f $svc.Name, $svc.Port) -ForegroundColor DarkGray
      continue
    }

    $killed = @()
    foreach ($procId in $pids) {
      $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue

      & taskkill /PID $procId /T /F 2>$null | Out-Null
      $killed += $procId

      if ($proc -and $proc.ParentProcessId) {
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)" -ErrorAction SilentlyContinue
        if ($parent -and $parent.Name -eq 'python.exe') {
          $parentId = $parent.ProcessId
          & taskkill /PID $parentId /T /F 2>$null | Out-Null
          $killed += $parentId
        }
      }
    }

    Write-Host ("  [x] {0,-12} :{1} detenido (pids: {2})" -f $svc.Name, $svc.Port, (($killed | Sort-Object -Unique) -join ', ')) -ForegroundColor Yellow
  }
}

function Show-ServiceStatus {
  Write-Host ''
  Write-Host 'Servicios Presto:' -ForegroundColor White
  foreach ($svc in $Services) {
    if (Test-ServicePort -Port $svc.Port) {
      Write-Host ("  [OK]   {0,-12} :{1}" -f $svc.Name, $svc.Port) -ForegroundColor Green
    } else {
      Write-Host ("  [ -- ] {0,-12} :{1}" -f $svc.Name, $svc.Port) -ForegroundColor DarkGray
    }
  }
}
