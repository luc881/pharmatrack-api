# Respaldo diario automatico de las BD de produccion (Railway).
# Corre via tarea programada de Windows; si ya hay respaldo de hoy, no
# hace nada (asi la tarea puede dispararse varias veces sin duplicar).
# Retencion: 30 dias.
#
# Respalda cada linea <NOMBRE>_DATABASE_URL= de scripts\.env.sync en
# backups\auto\<nombre>-AAAAMMDD.dump. PROD es Opuntia Den; otra instalacion
# (otro cliente) se agrega con su propia linea, p. ej. PATITAS_DATABASE_URL=

$ErrorActionPreference = "Stop"

$RepoDir   = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $RepoDir "backups\auto"
$LogFile   = Join-Path $BackupDir "backup.log"

New-Item -ItemType Directory -Force $BackupDir | Out-Null

function Log($msg) {
  $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
  Add-Content -Path $LogFile -Value $line -Encoding utf8
}

$EnvSync = Join-Path $PSScriptRoot ".env.sync"
if (-not (Test-Path $EnvSync)) { Log "ERROR: falta scripts\.env.sync"; exit 1 }

$Targets = Get-Content $EnvSync | ForEach-Object {
  if ($_ -match "^([A-Z0-9]+)_DATABASE_URL=(.+)$") { @{ Name = $Matches[1].ToLower(); Url = $Matches[2] } }
}
if (-not $Targets) { Log "ERROR: ninguna <NOMBRE>_DATABASE_URL con valor en .env.sync"; exit 1 }

$PgBin = @("C:\Program Files\PostgreSQL\17\bin", "C:\Program Files\PostgreSQL\16\bin") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $PgBin) { Log "ERROR: PostgreSQL no encontrado"; exit 1 }

$Today  = Get-Date -Format "yyyyMMdd"
$Failed = $false

foreach ($t in $Targets) {
  $Dump = Join-Path $BackupDir "$($t.Name)-$Today.dump"
  if (Test-Path $Dump) { continue }  # ya hay respaldo de hoy

  & "$PgBin\pg_dump" --dbname=$($t.Url) --format=custom --no-owner --no-acl --file=$Dump
  if ($LASTEXITCODE -ne 0) {
    # una BD caida no deja sin respaldo a las demas
    Log "ERROR: pg_dump de $($t.Name) fallo (exit $LASTEXITCODE)"
    if (Test-Path $Dump) { Remove-Item $Dump -Force -Confirm:$false }
    $Failed = $true
    continue
  }

  $sizeKb = [math]::Round((Get-Item $Dump).Length / 1KB)
  Log "OK: $Dump ($sizeKb KB)"
}

# Retencion: borrar respaldos automaticos de mas de 30 dias
Get-ChildItem $BackupDir -Filter "*.dump" |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  ForEach-Object { Log "Retencion: borrando $($_.Name)"; Remove-Item $_.FullName -Force -Confirm:$false }

if ($Failed) { exit 1 }
