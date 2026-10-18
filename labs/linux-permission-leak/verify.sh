#!/bin/sh
# Savunma doğrulayıcı (runner, hedef konteynerde docker exec ile argv olarak çalıştırır):
# 1) servis hâlâ yanıt veriyor  2) yedek 600 ve sahibi app  3) ogrenci okuyamıyor
set -u
wget -qO- http://127.0.0.1:8080/ >/dev/null 2>&1 || { echo "servis-calismiyor"; exit 1; }
mod=$(stat -c %a /srv/yedek/yedek.txt 2>/dev/null) || { echo "yedek-yok"; exit 1; }
sahip=$(stat -c %U /srv/yedek/yedek.txt)
[ "$mod" = 600 ] || [ "$mod" = 400 ] || { echo "izin-genis:$mod"; exit 1; }
[ "$sahip" = app ] || { echo "sahip-yanlis:$sahip"; exit 1; }
echo "tamam"
