---
slug: guvenli-arsiv-acma
module: web
title: 'Arşivler: dosya adını güvenilir sayma'
type: theory
minutes: 12
prerequisites:
- dosya-yolu-siniri
challenge: archive-slip
introduced: '1.1'
---
# Arşivler: dosya adını güvenilir sayma

Arşiv dosyası yalnız veri içermez; dosya adları da işlem kararını etkiler. Bir ZIP üyesi `../outside.txt` adını taşıyabilir. Uygulama bunu köke doğrudan eklerse beklenen çıkarma dizininden çıkabilir.

## Lab sınırı
Lab kendi ürettiği iki küçük ZIP fixture dosyasını kullanır. Zayıf yazma işlemi bile yalnız geçici lab fixture kökü içinde kalır. Host dosyası veya kullanıcı arşivi açılmaz. Python zipfile.extract yöntemi hedeflenmez; örnekte hatalı elle çıkarma kodu incelenir.

```python
for name in archive.namelist():
    target = (destination / name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise ValueError('Geçersiz üye')
```

## Uygulama
`probe` dışarı yazma bulgusunu verir. Kanıtı gönder ve `patch validate-members` uygula. `verify`, kötü üyeyi reddederken `notes.txt` içeren normal arşivi açabilmelidir.

## Kalan riskler
Üye sayısı, toplam açılmış boyut, sıkıştırma oranı ve symlink politikası ayrıca sınırlanmalıdır. Çok büyük arşivleri yalnız yol kontrolüyle güvenli sayma.

Kontrol sorusu: arşiv uzantısının .zip olması yol adlarını güvenilir yapar mı? Hayır.
