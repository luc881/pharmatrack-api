#!/bin/sh
# Respaldo diario de la base a Cloudflare R2. Vive en su propio servicio de
# Railway para que las llaves del bucket no estén en el API: si el API se
# compromete, los respaldos no.
#
# Variables del servicio:
#   DATABASE_URL            ${{Postgres.DATABASE_URL}} (referencia al Postgres del proyecto)
#   R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
#   BACKUP_NAME             carpeta y prefijo en el bucket: prod, patitas…
#
# Mismo formato que scripts/backup-prod.ps1 (pg_dump custom): se restaura con
# pg_restore. Lo viejo lo borra la regla de ciclo de vida del bucket.
set -eu

: "${DATABASE_URL:?falta DATABASE_URL}"
: "${R2_ACCOUNT_ID:?falta R2_ACCOUNT_ID}"
: "${R2_ACCESS_KEY_ID:?falta R2_ACCESS_KEY_ID}"
: "${R2_SECRET_ACCESS_KEY:?falta R2_SECRET_ACCESS_KEY}"
: "${R2_BUCKET:?falta R2_BUCKET}"
: "${BACKUP_NAME:?falta BACKUP_NAME}"

name="${BACKUP_NAME}-$(date -u +%Y%m%d-%H%M).dump"
file="${TMPDIR:-/tmp}/${name}"

pg_dump --dbname="$DATABASE_URL" --format=custom --no-owner --no-acl --file="$file"
echo "Dump listo: ${name} ($(wc -c < "$file") bytes)"

export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
export RCLONE_CONFIG_R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Pocos reintentos: con llaves o cuenta mal puestas debe fallar en segundos, no colgarse
rclone copyto "$file" "r2:${R2_BUCKET}/${BACKUP_NAME}/${name}" --s3-no-check-bucket --retries 2 --low-level-retries 2 --contimeout 15s --timeout 60s
echo "Subido a R2: ${R2_BUCKET}/${BACKUP_NAME}/${name}"
