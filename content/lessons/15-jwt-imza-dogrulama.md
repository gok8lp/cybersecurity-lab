---
slug: jwt-imza-dogrulama
module: identity
title: 'JWT: okunabilir veri, doğrulanmış kimlik değildir'
type: theory
minutes: 12
prerequisites:
- kimlik-ve-yetki
challenge: jwt-signature
introduced: '1.1'
---
# JWT: okunabilir veri, doğrulanmış kimlik değildir

JWT içeriği çoğunlukla base64url ile kodlanır; bu şifreleme değildir. Payload içindeki rolü okumak, bu rolün güvenilir olduğunu kanıtlamaz.

## Üç bölüm
`header.payload.signature`. Header algoritmayı tanımlar, payload iddiaları taşır, imza değişikliği algılar. Sunucu kabul edeceği algoritmayı kendi politikasıyla seçmelidir.

## Keşif
`probe`, rolü admin olan imzasız bir eğitim tokenı üretir. Zayıf dal header içindeki `alg=none` değerine güvenir. Rol kabul edilirse kanıtı gönder. Lab gerçek tokenları veya kullanıcı hesaplarını kullanmaz.

## Düzeltme
`patch pin-algorithm` yalnız HS256 ve doğru HMAC imzasını kabul eder. İmza karşılaştırması sabit zamanlı karşılaştırıcı kullanır. `verify` imzasız tokenı reddetmenin yanında geçerli student tokenını kabul eder ve payload'ı değiştirilmiş tokenı reddeder.

## Üretimde ek kontroller
Olgun bir JWT kütüphanesi kullan; issuer, audience, expiration ve anahtar rotasyonunu doğrula. Labdaki küçük uygulama yalnız imza/algoritma dersidir ve üretim JWT kütüphanesi değildir.

Kontrol sorusu: gizli anahtarı frontend paketine koymak güvenli mi? Hayır; o anahtarı alan biri geçerli imza üretebilir.
