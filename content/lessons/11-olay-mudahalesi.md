---
slug: olay-mudahalesi
module: final
title: En az yetkiden olay raporuna
type: theory
minutes: 10
prerequisites:
- log-analizi
---
# En az yetkiden olay raporuna

Konteyner izolasyonu tek bir ayar değildir: salt okunur kök, düşürülmüş capability, no-new-privileges, kaynak sınırları ve internetsiz ağ birlikte gerekir. Host socket bağlamak bu sınırı aşar.

## Kopya manifest
`container-least-privilege` gerçek host ayarlarını değiştirmeden bir örnek üzerinde yanlış yetkileri inceletir. En az yetkili seçim normal health davranışını korumalıdır.

## Final
`final-incident` için önce Linux izinleri, parametrik sorgu, C sınırı ve log lablarını savunma doğrulamasıyla tamamla. Logu oku, kaynağı incele, sızıntıyı oyuncak hedefte kanıtla, düzelt ve regresyonu geçir.

Olay raporu beş şeyi içermeli: giriş vektörü, kanıt, kök neden, düzeltme, doğrulama. Labdaki uzunluk kontrolü yalnız asgari rapor varlığını doğrular; yazının teknik kalitesini insan değerlendirmelidir.

Kontrol sorusu: erişimi tamamen kesmek normal işlevi koruyan bir yama mıdır? Hayır; negatif ve pozitif regresyon birlikte geçmelidir.
