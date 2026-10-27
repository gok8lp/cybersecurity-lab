---
slug: log-analizi
module: blue-team
title: 'Logdan kanıta: olay korelasyonu'
type: theory
minutes: 10
prerequisites:
- http-temelleri
---
# Logdan kanıta: olay korelasyonu

Tek bir başarısız giriş alarm için yeterli değildir. Zaman penceresi, oturum/istek kimliği ve normal davranışla karşılaştırma gerekir. IP adresi tek başına kimlik kanıtı değildir.

## İnceleme
`auth-log-hunt` içinde `read logs` ile verilen sentetik kaydı oku. Kısa aralıkta tekrarlanan başarısızlıkları aynı correlation ID altında grupla. `probe <id>` ile hipotezini sınayabilirsin.

## Savunma
`correlation` kuralı saldırı desenini yakalamalı ve normal req-17 oturumunu alarm dışı bırakmalı. Hassas parola veya token loglanmamalıdır.

Kontrol sorusu: başarılı giriş önceki başarısızlıkları önemsiz yapar mı? Hayır; başarısız denemelerden sonraki başarı ele geçirilme işareti olabilir.
