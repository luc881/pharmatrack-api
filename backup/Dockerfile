# Servicio de respaldo: corre una vez (cron de Railway), sube el dump a R2 y sale.
# postgresql17-client: pg_dump debe ser igual o más nuevo que el servidor (hoy 17).
FROM alpine:3.22
RUN apk add --no-cache postgresql17-client rclone
COPY backup.sh /backup.sh
CMD ["sh", "/backup.sh"]
