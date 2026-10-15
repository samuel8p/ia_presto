# setup.ps1 - prepara los microservicios de Presto en una maquina nueva.
#
# Uso:
#   .\setup.ps1
#
# Crea los entornos virtuales que falten e instala los requirements.
# NO crea los archivos .env (contienen secretos): copialos a mano.
#
# Si Windows bloquea el script por la politica de ejecucion:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$IARoot = $PSScriptRoot

Write-Host ''
Write-Host 'Presto - setup' -ForegroundColor Cyan
Write-Host '--------------' -ForegroundColor DarkGray

# 1) Encontrar un interprete de Python
$py = $null
foreach ($cand in @('py', 'python', 'python3')) {
  if (Get-Command $cand -ErrorAction SilentlyContinue) { $py = $cand; break }
}
if (-not $py) {
  throw 'No encontre Python. Instalalo desde https://www.python.org/downloads/ y volve a intentar.'
}
Write-Host ("Python: {0}" -f $py) -ForegroundColor DarkGray

# 2) Definir los venv que espera _services.ps1
$Venvs = @(
  [pscustomobject]@{
    Label = 'raiz (.venv) -> auth + transactions'
    Dir   = (Join-Path $IARoot '.venv')
    Reqs  = @(
      (Join-Path $IARoot 'auth\auth-app\requirements.txt'),
      (Join-Path $IARoot 'transactions\transactions-app\requirements.txt')
    )
  },
  [pscustomobject]@{
    Label = 'gateway'
    Dir   = (Join-Path $IARoot 'api\api-gateway-app\venv')
    Reqs  = @((Join-Path $IARoot 'api\api-gateway-app\requirements.txt'))
  },
  [pscustomobject]@{
    Label = 'chat'
    Dir   = (Join-Path $IARoot 'chat\chat-app\venv')
    Reqs  = @((Join-Path $IARoot 'chat\chat-app\requirements.txt'))
  }
)

foreach ($v in $Venvs) {
  $pythonExe = Join-Path $v.Dir 'Scripts\python.exe'
  Write-Host ''
  Write-Host ("== {0}" -f $v.Label) -ForegroundColor Yellow

  if (-not (Test-Path $pythonExe)) {
    Write-Host '  creando entorno virtual...' -ForegroundColor DarkGray
    & $py -m venv $v.Dir
  } else {
    Write-Host '  entorno virtual ya existe (se omite la creacion)' -ForegroundColor DarkGray
  }

  foreach ($req in $v.Reqs) {
    if (Test-Path $req) {
      Write-Host ("  pip install -r {0}" -f (Split-Path $req -Leaf)) -ForegroundColor DarkGray
      & $pythonExe -m pip install --quiet --upgrade pip
      & $pythonExe -m pip install --quiet -r $req
    } else {
      Write-Host ("  [aviso] no encontre {0}" -f $req) -ForegroundColor DarkYellow
    }
  }
}

# 3) Avisar por los .env que faltan
$EnvFiles = @(
  'auth\auth-app\.env',
  'chat\chat-app\.env',
  'transactions\transactions-app\.env',
  'api\api-gateway-app\.env'
)

$faltan = @()
foreach ($rel in $EnvFiles) {
  if (-not (Test-Path (Join-Path $IARoot $rel))) { $faltan += $rel }
}

Write-Host ''
if ($faltan.Count -gt 0) {
  Write-Host 'FALTAN archivos .env (son secretos, no estan en el repo):' -ForegroundColor Red
  foreach ($f in $faltan) { Write-Host ("  - {0}   (copiar de .env.example)" -f $f) -ForegroundColor Red }
  Write-Host 'Completalos y despues corre: .\start-all.ps1' -ForegroundColor Yellow
} else {
  Write-Host 'Listo. Ahora podes levantar todo con: .\start-all.ps1' -ForegroundColor Green
}
Write-Host ''
