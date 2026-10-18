# Fazla izinli yedek: app kullanıcısının servisi, herkesin okuyabildiği bir yedek bırakıyor.
FROM alpine:3.20
RUN addgroup -g 1000 app && adduser -D -u 1000 -G app app \
 && addgroup -g 1001 ogrenci && adduser -D -u 1001 -G ogrenci ogrenci \
 && mkdir -p /srv/www && echo "servis calisiyor" > /srv/www/index.html && chown -R app:app /srv/www
COPY baslat.sh /usr/local/bin/baslat.sh
RUN chmod 755 /usr/local/bin/baslat.sh
USER 1000:1000
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/baslat.sh"]
