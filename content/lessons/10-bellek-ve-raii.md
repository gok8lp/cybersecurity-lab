---
slug: bellek-ve-raii
module: memory
title: C sınırları, format ve C++ RAII
type: theory
minutes: 10
prerequisites:
- linux-izinleri
---
# C sınırları, format ve C++ RAII

C dizisinde sonlandırıcı dahil kapasite hesaplanmalıdır. `strcpy` hedef kapasitesini bilmez. Format metni de veri değildir: `printf(input)` yerine `printf("%s", input)` kullan.

## Üç ayrı lab
`c-stack-boundary` örneği AddressSanitizer ile gerçek konteynerde derlenir. Uzun girdi sınır dışında yazma bulgusu üretir. `bounded` yaması uzunluğu kontrol eder.

`c-format-string` yalnız kontrollü MARKER argümanını kullanır; gerçek süreç belleği veya host adresi araştırılmaz. Sabit format girdiyi olduğu gibi basmalıdır.

`cpp-raii-leak` örneğinde exception erken dönüşü taklit eder. Ham pointer kaynağı açık bırakırken `unique_ptr` destructor ile bırakır. Doğrulama canlı kaynak sayacının sıfır olduğunu kontrol eder.

Kontrol sorusu: testin çökmemesi tek başına güvenlik kanıtı mı? Hayır; normal, sınır ve hatalı girişler ayrı test edilmelidir.
