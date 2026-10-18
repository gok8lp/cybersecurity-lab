---
slug: kullanilabilirlik-dos
module: defense
title: Kullanılabilirlik ve DoS — neden çöker, nasıl ayakta kalır?
type: theory
minutes: 14
prerequisites: [http-temelleri]
---
# Kullanılabilirlik (availability)

Güvenliğin üç ayağı: **gizlilik, bütünlük, kullanılabilirlik** (CIA). DoS saldırıları üçüncüsünü hedefler:
sistemi çökertmez, **meşgul eder**. Beyaz şapkalı bir savunmacı olarak amacın, bir hizmetin saldırı altında
bile normal kullanıcıya açık kalmasını sağlamaktır.

> Bu ders kavramsaldır ve savunma odaklıdır. Saldırı üretme aracı ya da tarifi yoktur; amaç bir hizmeti
> dayanıklı kurmayı öğrenmektir.

## Bir hizmet neden boğulur?

Her sistemin sınırlı bir kaynağı vardır. Saldırı, bu kaynaklardan birini tüketir:

| Tüketilen kaynak | Ne olur |
|---|---|
| **Bant genişliği** | Hat dolar, meşru paketler sıraya giremez (hacimsel) |
| **Bağlantı tablosu** | Yarım açık bağlantılar tabloyu doldurur, yenisi kabul edilmez (protokol, ör. SYN flood) |
| **CPU / bellek** | Pahalı bir uç nokta (arama, rapor, giriş) her istekte çok iş yapar (uygulama katmanı) |

Uygulama katmanı en sinsisidir: saniyede birkaç yüz "ağır" istek, milyonlarca paket göndermeden hizmeti dışarıdan
normal görünerek boğabilir.

## DoS ile DDoS farkı

- **DoS:** tek kaynaktan. Genelde tek bir IP'yi engelleyerek durdurulur.
- **DDoS:** binlerce dağıtık kaynaktan (çoğu ele geçirilmiş cihaz). Tek IP engelleme yetmez; üst katman gerekir.

## Savunma katmanları (dıştan içe)

1. **Üst ağ / CDN:** Cloudflare gibi bir ters vekil trafiği süzer, anycast ile yükü dağıtır. Hacimsel saldırıyı
   senin sunucuna gelmeden emer. Ev sunucun için en güçlü kalkan budur.
2. **Hız sınırı (rate limit):** "Bir IP saniyede en çok N istek." Meşru kullanıcıyı etkilemeyecek, kötüyü yavaşlatacak
   bir eşik seçilir. nginx `limit_req`, API'de jeton kovası (token bucket).
3. **Bağlantı eşiği:** IP başına eş zamanlı bağlantı sınırı; SYN cookie ile yarım açık bağlantı taşması engellenir.
4. **Erken ret:** Pahalı işten önce ucuz kontrol. Kimlik doğrulaması gereken uç noktada, doğrulama başarısızsa
   ağır sorguya hiç girme.
5. **Otomatik engelleme:** fail2ban gibi bir araç, kısa sürede çok hata üreten IP'yi geçici olarak düşürür.
6. **Ölçek ve sağlık:** Yük artınca kopya ekleyebilmek ve sağlıksız örneği devreden çıkarmak.

## "Fail open" mı "fail closed" mı?

Kalkan çökerse ne olsun? Bir ödeme sistemi şüpheli durumda **kapanmalı** (fail closed); bir blog sayfası ise
erişilebilir **kalmalı** (fail open). Savunma tasarımında bu kararı bilinçli verirsin.

## Ölçülü olmak

İyi bir hız sınırı, saldırganı yavaşlatırken gerçek kullanıcıyı engellememelidir. Çok sıkı bir eşik, saldırının
kendisi kadar zarar verir: meşru trafiği de keser. Bu yüzden eşikler **ölçülerek** ayarlanır, körlemesine değil.

## Sıradaki

Bulmacalar bölümünde hangi nginx yapılandırmasının bir ucu koruduğunu ve bir log'da ani istek patlamasını
nasıl tanıyacağını deneyeceksin. Laboratuvarda ise hız sınırı olmayan bir ucu, kendi izole hedefinde sınır
ekleyerek sağlamlaştıracak ve doğrulayıcıyla "normal kullanıcı hâlâ çalışıyor" kanıtını alacaksın.
