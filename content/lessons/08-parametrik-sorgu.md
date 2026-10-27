---
slug: parametrik-sorgu
module: injection
title: 'SQL: veri ile komutu ayır'
type: theory
minutes: 10
prerequisites:
- http-temelleri
---
# SQL: veri ile komutu ayır

String birleştirmesi kullanıcı girdisini SQL söz dizimine dönüştürebilir. Parametrik sorgu değeri ayrı bağlar; kaçış karakterlerini elle yönetmek yerine sürücüyü kullanır.

```python
db.execute("SELECT name FROM users WHERE name=? AND password=?", (name, password))
```

## Keşif ve savunma
`sqlite-parameter` labı bellek içi bir eğitim veritabanı kullanır. `read source` ile sorguyu gör, kontrollü `probe` ile farkı gözle. `patch parameterized` sonra aynı girdi artık giriş sağlayamamalı; normal veri sorgusu çalışmalı.

Gerçek uygulamalarda ayrıca parola özeti, rate limit ve yetkilendirme gerekir. Kontrol sorusu: prepared statement nesne sahipliği kontrolünün yerine geçer mi? Hayır.
