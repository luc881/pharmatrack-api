# SUBIR: Postgres local -> produccion (Railway).
# Correr AL VOLVER de la convencion, con internet.
# REEMPLAZA la BD de produccion con la local - antes guarda un respaldo
# de produccion en backups\ por si hay que revertir.

# Si el comun no carga, abortar aqui en vez de seguir a medias
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\sync-common.ps1"

Write-Host "Esto REEMPLAZA la base de datos de PRODUCCION con tu BD local." -ForegroundColor Yellow
Write-Host "Hazlo solo si todo el trabajo desde el ultimo 'bajar' fue en la BD local." -ForegroundColor Yellow
$confirm = Read-Host "Escribe SUBIR para continuar"
if ($confirm -ne "SUBIR") { Write-Host "Cancelado." -ForegroundColor Red; exit 1 }

$ProdBackup = Join-Path $BackupDir "prod-antes-de-subir-$Stamp.dump"
$LocalDump  = Join-Path $BackupDir "local-$Stamp.dump"

Invoke-Dump    $ProdUrl  $ProdBackup "produccion (respaldo previo)"
Invoke-Dump    $LocalUrl $LocalDump  "la BD local"
Invoke-Restore $ProdUrl  $LocalDump  "produccion"

Write-Host ""
Write-Host "LISTO: produccion actualizada con tu BD local." -ForegroundColor Green
Write-Host "El sitio publico reflejara los cambios en ~1 minuto (revalidacion)." -ForegroundColor Cyan
Write-Host "Respaldo previo de produccion: $ProdBackup" -ForegroundColor Cyan
