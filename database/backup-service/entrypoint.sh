#!/bin/sh

cp /run/secrets/rclone-config /root/.rclone.conf
echo "$PGHOST:$PGPORT:*:$(cat /run/secrets/postgres-user):$(cat /run/secrets/postgres-password)" > $PGPASSFILE
chmod 0600 $PGPASSFILE
crontab /crontab

crond -f -l 8