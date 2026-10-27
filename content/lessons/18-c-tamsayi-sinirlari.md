---
slug: c-tamsayi-sinirlari
module: memory
title: 'C tamsayıları: daraltmadan önce denetle'
type: theory
minutes: 12
prerequisites:
- bellek-ve-raii
challenge: c-integer-boundary
introduced: '1.1'
---
# C tamsayıları: daraltmadan önce denetle

C'de bir sayının türünü değiştirmek yalnız gösterimi değiştirmez; değer aralığı da değişebilir. `uint8_t` 0..255 aralığını taşır. 256'nın bu türe dönüşümü 0 üretir. Sonradan yapılan küçük-boyut kontrolü büyük isteği yanlışlıkla kabul edebilir.

## Deney
`read source` daraltmanın kontrolden önce yapıldığını gösterir. `probe` gerçek gcc derlemesini 256 ile çalıştırır. Bu örnek taşan belleğe yazmaz; yanlış kabul kararını dönüş koduyla gösterir.

```c
if (n > UINT8_MAX) return 0;
uint8_t size = (uint8_t)n;
return size < 8;
```

## Savunma
Kanıtı gönder, `patch check-before-cast` uygula. Kontrol geniş türdeyken yapılır. `verify` 256 girdisini reddeder ve normal 4 girdisini kabul eder. Derleme `-Wall -Wextra -Werror` kullanır.

## Daha geniş düşün
Toplama ve çarpma da taşabilir. Boyut hesaplarında `count > SIZE_MAX / item_size` kontrolünü çarpma işleminden önce yap. Signed overflow ve unsigned wrap aynı dil kuralı değildir.

Kontrol sorusu: dönüşümden sonra değeri yeniden unsigned int yapmak kaybolan bitleri geri getirir mi? Hayır.
