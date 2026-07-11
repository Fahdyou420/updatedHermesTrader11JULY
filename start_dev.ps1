[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Repo

Write-Host "`n=== HERMES DEV BOOT ===" -ForegroundColor Cyan

function Test-Command($c){ try { Get-Command $c -ErrorAction Stop | Out-Null; $true } catch { $false } }

# 1) Docker stack
if (Test-Command docker) {
  Write-Host "[Docker] compose up -d" -ForegroundColor Yellow
  docker compose up -d | Out-Null
} else {
  Write-Host "[Docker] not installed — skipping compose" -ForegroundColor DarkYellow
}

# 2) Env sanity
$env:PORT = "5173"
$rcUrl = ".env"
if (Test-Path $rcUrl) {
  Get-Content $rcUrl | ForEach-Object {
    if ($_ -match '^REDIS_URL=') { $env:REDIS_URL = ($_ -split '=',2)[1].Trim('"').Trim("'") }
  }
}
if (-not $env:REDIS_URL) { $env:REDIS_URL = "redis://127.0.0.1:6379" }
Write-Host "[Env] PORT=$env:PORT  REDIS_URL=$env:REDIS_URL" -ForegroundColor DarkGray

# 3) Dev server
Write-Host "[Dev] npm run dev" -ForegroundColor Green
$npm = if (Test-Command npm) { "npm" } else { Join-Path $Repo "node_modules/.bin/npm.cmd" }
& $npm run dev
