# Respaldo diario automatico de la BD de produccion (Railway).
# Corre via tarea programada de Windows; si ya hay respaldo de hoy, no
# hace nada (asi la tarea puede dispararse varias veces sin duplicar).
# Retencion: 30 dias.

$ErrorActionPreference = "Stop"

$RepoDir   = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $RepoDir "backups\auto"
$LogFile   = Join-Path $BackupDir "backup.log"

New-Item -ItemType Directory -Force $BackupDir | Out-Null

function Log($msg) {
  $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
  Add-Content -Path $LogFile -Value $line -Encoding utf8
}

$Today = Get-Date -Format "yyyyMMdd"
$Dump  = Join-Path $BackupDir "prod-$Today.dump"

if (Test-Path $Dump) { exit 0 }  # ya hay respaldo de hoy

$EnvSync = Join-Path $PSScriptRoot ".env.sync"
if (-not (Test-Path $EnvSync)) { Log "ERROR: falta scripts\.env.sync"; exit 1 }
$ProdUrl = (Get-Content $EnvSync | Where-Object { $_ -match "^PROD_DATABASE_URL=" }) -replace "^PROD_DATABASE_URL=", ""
if (-not $ProdUrl) { Log "ERROR: PROD_DATABASE_URL vacio"; exit 1 }

$PgBin = @("C:\Program Files\PostgreSQL\17\bin", "C:\Program Files\PostgreSQL\16\bin") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $PgBin) { Log "ERROR: PostgreSQL no encontrado"; exit 1 }

& "$PgBin\pg_dump" --dbname=$ProdUrl --format=custom --no-owner --no-acl --file=$Dump
if ($LASTEXITCODE -ne 0) {
  Log "ERROR: pg_dump fallo (exit $LASTEXITCODE)"
  if (Test-Path $Dump) { Remove-Item $Dump -Force -Confirm:$false }
  exit 1
}

$sizeKb = [math]::Round((Get-Item $Dump).Length / 1KB)
Log "OK: $Dump ($sizeKb KB)"

# Retencion: borrar respaldos automaticos de mas de 30 dias
Get-ChildItem $BackupDir -Filter "prod-*.dump" |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  ForEach-Object { Log "Retencion: borrando $($_.Name)"; Remove-Item $_.FullName -Force -Confirm:$false }
