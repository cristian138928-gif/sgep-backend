# scripts/start-local.ps1
# Arranque local garantizado (backend + frontend) con checks basicos.
param(
  [switch]$Seed,
  [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Write-Step($msg) { Write-Host "[SGEP] $msg" -ForegroundColor Cyan }
function Wait-Http($url, $name, $tries = 60) {
  for ($i=0; $i -lt $tries; $i++) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { Write-Step "$name listo: $url"; return $true } } catch {}
    Start-Sleep -Seconds 2
  }
  Write-Warning "$name no respondio a tiempo: $url"; return $false
}

if (-not (Test-Path ".env")) {
  if (Test-Path ".env.example") { Copy-Item ".env.example" ".env"; Write-Warning ".env creado desde .env.example: revisa SECRET_KEY/DATABASE_URL." } else { throw "Falta .env y .env.example" }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv no encontrado. Instala uv: https://docs.astral.sh/uv/" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm no encontrado. Instala Node.js 20+." }

# Dependencias backend
if (-not (Test-Path ".venv")) { Write-Step "Instalando dependencias backend (uv sync)..."; uv sync --frozen }

# Dependencias frontend
if (-not (Test-Path "frontend\node_modules")) { Write-Step "Instalando dependencias frontend (npm install)..."; Push-Location frontend; npm install; Pop-Location }

# Backend
$apiUp = $false
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $apiUp = $true } } catch {}
if (-not $apiUp) {
  Write-Step "Iniciando backend (uvicorn :8000)..."
  Start-Process powershell -ArgumentList @('-NoExit','-Command',"Set-Location '$root'; uv run uvicorn app.main:app --reload --port 8000") | Out-Null
} else { Write-Step "Backend ya activo en :8000" }

# Frontend
$feUp = $false
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -ge 200) { $feUp = $true } } catch {}
if (-not $feUp) {
  Write-Step "Iniciando frontend (vite :5173)..."
  Start-Process powershell -ArgumentList @('-NoExit','-Command',"Set-Location '$root\frontend'; npm run dev") | Out-Null
} else { Write-Step "Frontend ya activo en :5173" }

Wait-Http "http://127.0.0.1:8000/health" "Backend" 60 | Out-Null
Wait-Http "http://127.0.0.1:5173" "Frontend" 60 | Out-Null

if ($Seed) {
  Write-Step "Aplicando seed demo (idempotente)..."
  $env:PYTHONPATH = $root
  uv run python scripts/seed_demo.py
}

Write-Step "Listo. Local: http://localhost:5173 (API: http://localhost:8000)"
if (-not $NoBrowser) { try { Start-Process "http://localhost:5173" } catch {} }
