#! /bin/sh

set -e

pg_dumpall -U $(cat /run/secrets/postgres-user) --no-password -c | gzip | rclone rcat lewis-lab-gdrive:/backups/dump_$(date +"%Y-%m-%d_%H_%M_%S").gz
