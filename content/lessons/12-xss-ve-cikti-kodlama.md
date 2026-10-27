---
slug: xss-ve-cikti-kodlama
module: web
title: 'XSS: çıktı bağlamını koru'
type: theory
minutes: 12
prerequisites:
- http-temelleri
challenge: web-output-encoding
introduced: '1.1'
---
# XSS: çıktı bağlamını koru

XSS, güvenilmeyen metnin tarayıcı tarafından çalıştırılabilir içerik olarak yorumlanmasıdır. Bu lab gerçek HTML parser kullanır; tarayıcıda saldırı kodu yürütmez. Amaç metin ve işaretleme arasındaki sınırı görmektir.

## Önce tahmin et
`<script>training()</script>` bir paragraf içine doğrudan eklendiğinde parser hangi etiketi görür? `read source`, ardından `probe` çalıştır. Çıktıda etkin etiket bulunduğunda kanıtı gönder.

## Doğru bağlam
HTML metin düğümü için `html.escape(value, quote=True)` metni koruyarak `<`, `>` ve `&` işaretlerini kodlar. JavaScript, URL ve CSS bağlamları farklı kodlayıcı gerektirir. Bu düzeltmeyi bütün bağlamlara genelleme.

```python
rendered = '<p>' + html.escape(value, quote=True) + '</p>'
```

## Savunma ve regresyon
`patch escape-html` uygula ve aynı girdiyi tekrar dene. Savunma doğrulaması etkin etiketi reddeder; normal Türkçe metin, tırnak ve ampersand karakterlerinin okunabilir kaldığını kontrol eder. Tüm işaretleri silmek veri kaybına yol açar.

## Kendini sınama
CSP tek başına çıktı kodlamasının yerine geçer mi? Hayır. Kullanıcının HTML yazması gerekiyorsa ne değişir? Bağlama uygun güvenilir bir HTML sanitizer ve ayrı bir içerik politikası gerekir.
