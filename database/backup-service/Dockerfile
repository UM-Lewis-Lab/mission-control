FROM rclone/rclone:1.55.1

RUN apk add --no-cache postgresql-client=13.3-r0

WORKDIR /
COPY backup.sh entrypoint.sh crontab  /

ENTRYPOINT [ "/entrypoint.sh" ]