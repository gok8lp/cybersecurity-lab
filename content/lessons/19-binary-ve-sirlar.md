---
slug: binary-ve-sirlar
module: reverse
title: 'Binary inceleme: strings ve sır sınırı'
type: theory
minutes: 12
prerequisites:
- bellek-ve-raii
challenge: binary-secret
introduced: '1.1'
---
# Binary inceleme: strings ve sır sınırı

Kaynak kodunu derlemek içerdiği sabitleri gizlemez. ELF içindeki okunabilir dizeler strings ile bulunabilir. Stripping sembolleri azaltır; gömülü sırrı güvenilir biçimde saklamaz.

## İnceleme
`read source` örnek programı gösterir. `probe` gcc ile geçici binary derler, ardından gerçek `strings` çıktısında yalnız `TRAINING-KEY-47` eğitim sabitini arar. Bulunan sabit gerçek sunucu anahtarı değildir. Kanıt flag'i oturuma özeldir.

## Savunma
`patch external-secret` gömülü sabiti kaldırır. Sabit yerine çalışma anında verilen lab ortam değişkeni kullanılır. `verify`, binary'de sabitin bulunmadığını, gerekli yapılandırmayla programın çalıştığını ve secret yokken hata verdiğini sınar.

## Güven sınırı
Ortam değişkeni aynı makinedeki yetkili süreç sahibine karşı sır saklamaz. Asıl ders: istemciye dağıtılan binary'nin içinde bir sunucu sırrı tutma. Üretimde yetkilendirmeyi güvenilir sunucu tarafında yap; yerel servis secretını uygun izinli secret store ile sağla.

Kontrol sorusu: sabiti base64 yapmak gizlilik sağlar mı? Hayır, kodlamayı bilen herkes geri çevirebilir.
