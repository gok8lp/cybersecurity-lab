# FLUGEL Cyber Range 1.0

Türkçe, tek sahibi için kişisel eğitim alanı: **12 ders, 17 bulmaca, 13 izole lab senaryosu**.

## Çalışan akış

Ders önkoşulları ve tamamlama; kalıcı XP, seviye, Türkiye saatine göre günlük seri, 1/7/30 günlük tekrar önerileri. İpuçları sunucuda sırayla açılır: ikinci ipucu %10, üçüncüsü %25 keser; yenileme kesintiyi sıfırlamaz. Aynı içerik tekrar XP vermez.

Lab döngüsü: başlat → keşfet → kanıt flag değerini gönder → savunmayı uygula → regresyonu doğrula → XP ve temizlik. 45 dakika TTL, en fazla iki etkin oturum, kapasite eşiği, 15 saniyelik temizleyici. Yenileme sonrası oturumlar bulunur. Yanlış/süresi dolmuş flag reddedilir. Audit kaydı flag veya komut metni içermez.

## Gerçek kapsam ve sınırlar

**Serbest shell veya genel amaçlı attacker terminali değildir.** Konsol yalnız `help`, `files`, `read`, `probe`, `patch`, `verify`, `report` kabul eder; `patch` sağlanan savunma seçeneklerini uygular. Keyfi kaynak yükleme, host komutu veya gerçek ağ taraması yoktur.

| Alıştırma | Gerçekleştirme |
|---|---|
| Linux izinleri | Geçici dosyada gerçek POSIX chmod; dünya-okuma biti üzerinden öğrenci yetkisi modeli. Ayrı attacker UID süreci yok. |
| SQL ve final | Gerçek bellek içi SQLite; enjeksiyon girdisi ve parametrik sorgu. |
| C sınır/format, C++ RAII | Konteynerde gerçek gcc/g++ derlemesi, ASan veya kaynak sayacı; önceden sağlanan kaynak varyantları. |
| HTTP / nesne sahipliği | Oyuncak yanıt ve sahiplik kararları. Dışarı açık zafiyetli HTTP servisi değil. |
| Kapsam / PATH / servis haritası / konteyner politikası | Sentetik karar ve veri alıştırmaları; gerçek ağa paket veya host ayarı değişikliği yok. |
| Log avı | Sentetik logda correlation ID ve yanlış pozitif kontrolü. |
| Final | Dört önkoşul lab, SQL kanıtı, düzeltme, regresyon, en az 80 karakterlik olay raporu. Yazının teknik kalitesi insan değerlendirmesi gerektirir. |

`MASTER_SPEC.md` ileri ürün tasarımıdır; serbest terminal, keyfi C kaynak düzenleme, çok kullanıcı, VPN/public yayın bu sürümün özelliği değildir.

## Geliştirme

Python 3.12+, Node 22.12+, pnpm 11.25.0. Lablar için Linux Docker + Compose.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cd apps/web
pnpm install --frozen-lockfile
pnpm run build
cd ../..
CYBERLAB_DATA=./data PYTHONPATH=apps/api .venv/bin/uvicorn cyberlab.main:create_app --factory --host 127.0.0.1 --port 8317
```

API ve arayüz birlikte `http://127.0.0.1:8317`. Runner yoksa dersler/bulmacalar çalışır; lablar kullanılamıyor gösterilir. Vite dev proxy kullanılırsa API 8000 portunda çalıştırılmalıdır.

## Kurulum ve erişim

Dist dahil hazırlanmış release dizininde, Docker grubunda ve sudo yetkili kullanıcıyla `bash deploy/install.sh`.

- Kod: `/opt/flugel-cyberlab/releases/<tarih>`, etkin sürüm `current` sembolik bağı.
- API: Docker yetkisi olmayan `cyberlab` sistem kullanıcısı; veri `/var/lib/cyberlab` (0700).
- Broker: kuran kullanıcı ve Docker yetkisi; özel Unix soket `/run/cyberlab/runner.sock`; sicil `/var/lib/cyberlab-runner`.
- Yalnız **127.0.0.1:8317** dinlenir. LAN/public listener veya Cloudflare rotası kurulmaz.
- Uygulama tek sahibin SSH erişimine güvenir; çok kullanıcı kimlik doğrulaması yoktur. İnternete ters proxy ile açmayın.

```bash
ssh -N -L 8317:127.0.0.1:8317 flugel@SUNUCU_ADRESI
```

Bilgisayarınızda `http://127.0.0.1:8317`. Mevcut SSH anahtarı kullanılır; uygulamaya sunucu parolası girilmez.

## İşletim ve geri dönüş

`sudo systemctl status cyberlab-api cyberlab-runner`; loglar `sudo journalctl -u cyberlab-api -u cyberlab-runner --since today`.

Güncelleme öncesi açık labları durdurun, SQLite online backup API'siyle DB'yi ve izinleri korunarak `server_secret` dosyasını yedekleyin. Önceki release'ler saklanır. `current` bağını önceki sürüme alıp iki servisi yeniden başlatmak kod geri dönüşüdür; şema değişmişse eşleşen veri yedeği gerekir. Eski prototip DB otomatik taşınmaz; bu kurulum yenidir.

## Kontroller

```bash
.venv/bin/python -m pytest -q
cd apps/web && pnpm run build
# Linux sunucusunda, gerçek ilerlemeden ayrı geçici test DB ile:
PYTHONPATH=apps/api:. .venv/bin/python tools/server_acceptance.py
```

Kabul testi 13 senaryoda kanıt, yanlış yamanın reddi, doğru savunma ve temizlik; ardından 20 aç/kapat döngüsü ve sıfır yetim managed kaynak denetimi yapar. Kullanıcının etkin labı varken çalıştırmayın.

Yeni ders: `content/lessons/*.md`. Yeni bulmaca: `tests/bulmaca_kaynak.yaml` ve `python tools/bulmaca_derle.py`. `tools/prepare_release.py` Compose manifestlerini ve son altı dersi yeniden üretir; elle değişiklikleri ezebilir, bilinçli kullanılmalıdır. Cevap özetleri eğitim bulmacası gizlemesidir, kriptografik sır sayılmaz.
