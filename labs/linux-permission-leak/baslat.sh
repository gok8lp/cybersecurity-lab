#!/bin/sh
# Flag imajda yok: oturum başında runner ortam değişkeniyle verir, tmpfs'e yazılır.
set -eu
: "${CYBERLAB_FLAG:?flag yok}"
umask 022
printf '%s\n' "$CYBERLAB_FLAG" > /srv/yedek/yedek.txt   # bilerek 644 (zafiyet)
unset CYBERLAB_FLAG
exec httpd -f -p 8080 -h /srv/www
