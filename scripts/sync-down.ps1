# BAJAR: produccion (Railway) -> Postgres local + cache de imagenes.
# Correr ANTES de salir a la convencion, con internet.
# El dump queda en backups\ y sirve tambien como respaldo de produccion.

# Si el comun no carga (error de sintaxis, archivo faltante) hay que
# abortar aqui - sin esto el script sigue y miente con "LISTO"
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\sync-common.ps1"

$Dump = Join-Path $BackupDir "prod-$Stamp.dump"

Invoke-Dump    $ProdUrl  $Dump "produccion"
Invoke-Restore $LocalUrl $Dump "la BD local"

Write-Host "Descargando imagenes a la cache local..." -ForegroundColor Cyan
Set-Location $RepoDir
$env:DATABASE_URL    = $LocalUrl
$env:IMAGE_CACHE_DIR = $CacheDir
poetry run python -m pharmatrack.scripts.cache_images
if ($LASTEXITCODE -ne 0) { Write-Host "La cache de imagenes fallo (la BD local si quedo lista)" -ForegroundColor Yellow }

Write-Host ""
Write-Host "LISTO: BD local actualizada con produccion. Ya puedes trabajar offline." -ForegroundColor Green
Write-Host "Si el stack local estaba corriendo, reinicialo (PharmaTrack - Iniciar)." -ForegroundColor Cyan
Write-Host "Regla: mientras trabajes offline NO edites nada en app.opuntiaden.com." -ForegroundColor Yellow
