# scripts/start.ps1
# Arranque unificado SGEP: auto-detecta Docker (si daemon activo) o modo local.
param(
  [ValidateSet('auto','docker','local')][string]$Mode = 'auto',
  [switch]$Seed,
  [switch]$NoSeed,
  [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Has-Docker {
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
  docker info *> $null
  return ($LASTEXITCODE -eq 0)
}

$useDocker = $false
if ($Mode -eq 'docker') { $useDocker = $true }
elseif ($Mode -eq 'local') { $useDocker = $false }
else { $useDocker = Has-Docker }

if ($useDocker) {
  Write-Host "[SGEP] Modo: Docker" -ForegroundColor Green
  $args = @()
  if ($NoSeed) { $args += '-NoSeed' }
  if ($NoBrowser) { $args += '-NoBrowser' }
  & "$PSScriptRoot\start-docker.ps1" @args
} else {
  if ($Mode -eq 'auto') { Write-Host "[SGEP] Docker no disponible, usando modo local." -ForegroundColor Yellow }
  Write-Host "[SGEP] Modo: Local" -ForegroundColor Green
  $args = @()
  if ($Seed) { $args += '-Seed' }
  if ($NoBrowser) { $args += '-NoBrowser' }
  & "$PSScriptRoot\start-local.ps1" @args
}
