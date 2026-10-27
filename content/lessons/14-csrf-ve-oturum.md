---
slug: csrf-ve-oturum
module: identity
title: 'CSRF: cookie, istek niyetini kanıtlamaz'
type: theory
minutes: 12
prerequisites:
- kimlik-ve-yetki
challenge: csrf-token
introduced: '1.1'
---
# CSRF: cookie, istek niyetini kanıtlamaz

Tarayıcı cookie bilgisini bazı isteklerde otomatik taşır. Bu nedenle oturum cookie'sinin bulunması, kullanıcının durum değiştiren isteği bilerek başlattığını kanıtlamaz. CSRF bu ayrımdan yararlanır.

Bu lab ağ isteği veya gerçek hesap işlemi yapmaz; istek doğrulama fonksiyonunu doğrudan çalıştırır.

## Deney
`read source` token kontrolünün eksikliğini gösterir. `probe` tokensız isteği, `probe wrong` yanlış tokenı temsil eder. İkisi kabul ediliyorsa kanıtı gönder.

## Savunma
`patch validate-token` uygula. Sunucu beklenen tokenı oturumla ilişkilendirmeli, her durum değiştiren istekte doğrulamalıdır. Bu örnekte sabit eğitim oturumu kullanılır; üretimde token kriptografik rastgelelikten üretilmelidir.

```python
valid = bool(token) and hmac.compare_digest(expected, token)
```

`probe session-bound-training-token` normal isteği temsil eder. `verify`, normal tokenın kabulünü ve hem boş hem yanlış tokenın reddini kontrol eder.

## Tamamlayıcı önlemler
SameSite cookie ve Origin kontrolleri ek savunma sağlar. GET ile durum değiştirme. XSS aynı origin içinde tokenı okuyabileceğinden CSRF düzeltmesi XSS'i çözmez.

Kontrol sorusu: tokenı yalnız arayüzde kontrol etmek yeterli mi? Hayır; karar sunucuda verilmelidir.
