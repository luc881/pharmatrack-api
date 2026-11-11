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

# Copia fuera de la laptop (Cloudflare R2), si .env.sync trae sus cuatro R2_*.
# rclone copy solo sube lo que falta; lo viejo lo borra la regla de ciclo de
# vida del bucket, no este script.
$R2 = @{}
Get-Content $EnvSync | ForEach-Object { if ($_ -match "^(R2_[A-Z_]+)=(.+)$") { $R2[$Matches[1]] = $Matches[2] } }
if ($R2.R2_ACCOUNT_ID -and $R2.R2_ACCESS_KEY_ID -and $R2.R2_SECRET_ACCESS_KEY -and $R2.R2_BUCKET) {
  $Rclone = (Get-Command rclone -ErrorAction SilentlyContinue).Source
  if (-not $Rclone) { $Rclone = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\rclone.exe" }
  if (-not (Test-Path $Rclone)) {
    Log "ERROR: R2 configurado pero falta rclone (winget install Rclone.Rclone)"
    $Failed = $true
  } else {
    $env:RCLONE_CONFIG_R2_TYPE = "s3"
    $env:RCLONE_CONFIG_R2_PROVIDER = "Cloudflare"
    $env:RCLONE_CONFIG_R2_ACCESS_KEY_ID = $R2.R2_ACCESS_KEY_ID
    $env:RCLONE_CONFIG_R2_SECRET_ACCESS_KEY = $R2.R2_SECRET_ACCESS_KEY
    $env:RCLONE_CONFIG_R2_ENDPOINT = "https://$($R2.R2_ACCOUNT_ID).r2.cloudflarestorage.com"
    & $Rclone copy $BackupDir "r2:$($R2.R2_BUCKET)" --include "*.dump" --s3-no-check-bucket
    if ($LASTEXITCODE -ne 0) { Log "ERROR: la copia a R2 fallo (exit $LASTEXITCODE)"; $Failed = $true }
    else { Log "OK: respaldos copiados a R2 ($($R2.R2_BUCKET))" }
  }
}

if ($Failed) { exit 1 }
