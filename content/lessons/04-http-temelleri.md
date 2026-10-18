---
slug: http-temelleri
module: web
title: HTTP temelleri ve güvenlik başlıkları
type: theory
minutes: 12
prerequisites: [baslarken]
---
# HTTP isteği ve yanıtı

    GET /giris HTTP/1.1
    Host: example.com

    HTTP/1.1 200 OK
    Content-Type: text/html
    Server: ornek/1.2.3

## Bilgi sızdıran başlıklar

`Server: ornek/1.2.3` gibi başlıklar yazılımın tam sürümünü söyler. Saldırgan bu bilgiyle bilinen açıkları arar. Sürüm bilgisini göstermemek iyi bir alışkanlıktır.

## Koruyucu başlıklar

| Başlık | Ne yapar |
|---|---|
| `Content-Security-Policy` | Sayfanın hangi kaynaklardan betik/stil yükleyebileceğini sınırlar |
| `X-Content-Type-Options: nosniff` | Tarayıcının dosya türünü tahmin etmesini engeller |
| `Strict-Transport-Security` | Siteye yalnız HTTPS ile bağlanılmasını zorunlu kılar |
| `X-Frame-Options` / `frame-ancestors` | Sayfanın başka sitelerde çerçeve içinde açılmasını engeller |

## Çerezler

Oturum çerezleri `HttpOnly` (betikler okuyamaz), `Secure` (yalnız HTTPS) ve `SameSite` (başka siteden gelen isteklerde gönderilmez) işaretlerini taşımalıdır.
