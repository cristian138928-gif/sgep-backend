# scripts/start-docker.ps1
# Arranque Docker garantizado (db + api + frontend) con healthchecks y seed.
param(
  [switch]$NoSeed,
  [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Write-Step($msg) { Write-Host "[SGEP] $msg" -ForegroundColor Cyan }
function Wait-Http($url, $name, $tries = 90) {
  for ($i=0; $i -lt $tries; $i++) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { Write-Step "$name listo: $url"; return $true } } catch {}
    Start-Sleep -Seconds 2
  }
  Write-Warning "$name no respondio a tiempo: $url"; return $false
}

if (-not (Test-Path ".env")) {
  if (Test-Path ".env.example") { Copy-Item ".env.example" ".env"; Write-Warning ".env creado desde .env.example: revisa SECRET_KEY (>=32)." } else { throw "Falta .env y .env.example" }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker no encontrado. Instala Docker Desktop." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker daemon no disponible. Inicia Docker Desktop y reintenta." }

Write-Step "Levantando stack Docker (build si es necesario)..."
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Fallo docker compose up" }

Wait-Http "http://localhost:3000" "Frontend (nginx)" 90 | Out-Null
# API via proxy nginx
Wait-Http "http://localhost:3000/api/v1/auth/login" "Proxy/API" 90 | Out-Null

if (-not $NoSeed) {
  Write-Step "Aplicando seed demo en contenedor (idempotente)..."
  docker compose exec -T api python scripts/seed_demo.py
}

docker compose ps
Write-Step "Listo. Docker: http://localhost:3000 (API: http://localhost:8000)"
if (-not $NoBrowser) { try { Start-Process "http://localhost:3000" } catch {} }
