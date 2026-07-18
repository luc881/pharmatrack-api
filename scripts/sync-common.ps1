# Config compartida de sync-down / sync-up (modo convencion).
# Requiere scripts\.env.sync con la linea:
#   PROD_DATABASE_URL=postgresql://... (Railway -> Postgres -> DATABASE_PUBLIC_URL)

$ErrorActionPreference = "Stop"

$RepoDir   = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $RepoDir "backups"
$CacheDir  = Join-Path $RepoDir "image_cache"
$LocalUrl  = "postgresql://postgres:postgres@localhost/pharmatrack"

# pg_dump/pg_restore: usar el cliente mas nuevo instalado
$PgBin = @("C:\Program Files\PostgreSQL\17\bin", "C:\Program Files\PostgreSQL\16\bin") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $PgBin) { Write-Host "No se encontro PostgreSQL en Program Files" -ForegroundColor Red; exit 1 }

# Leer PROD_DATABASE_URL de scripts\.env.sync (gitignoreado)
$EnvSync = Join-Path $PSScriptRoot ".env.sync"
if (-not (Test-Path $EnvSync)) {
  Write-Host "Falta scripts\.env.sync — copia .env.sync.example y pega la URL publica de Railway" -ForegroundColor Red
  exit 1
}
$ProdUrl = (Get-Content $EnvSync | Where-Object { $_ -match "^PROD_DATABASE_URL=" }) -replace "^PROD_DATABASE_URL=", ""
if (-not $ProdUrl) { Write-Host "PROD_DATABASE_URL vacio en scripts\.env.sync" -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force $BackupDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Invoke-Dump($url, $file, $label) {
  Write-Host "Dump de $label -> $file" -ForegroundColor Cyan
  & "$PgBin\pg_dump" --dbname=$url --format=custom --no-owner --no-acl --file=$file
  if ($LASTEXITCODE -ne 0) { Write-Host "pg_dump de $label fallo" -ForegroundColor Red; exit 1 }
}

function Invoke-Restore($url, $file, $label) {
  Write-Host "Restaurando $file en $label" -ForegroundColor Cyan
  # Esquema limpio: restauracion determinista sin residuos de la BD anterior
  & "$PgBin\psql" --dbname=$url -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  if ($LASTEXITCODE -ne 0) { Write-Host "No se pudo limpiar el esquema de $label" -ForegroundColor Red; exit 1 }
  & "$PgBin\pg_restore" --dbname=$url --no-owner --no-acl $file
  if ($LASTEXITCODE -ne 0) { Write-Host "pg_restore en $label fallo" -ForegroundColor Red; exit 1 }
}
