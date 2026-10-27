---
slug: dosya-yolu-siniri
module: web
title: 'Dosya yolları: normalize et, sınırı denetle'
type: theory
minutes: 12
prerequisites:
- http-temelleri
challenge: path-traversal
introduced: '1.1'
---
# Dosya yolları: normalize et, sınırı denetle

Bir dosya adını dizine eklemek, o dosyanın dizin içinde kalacağını kanıtlamaz. `../` üst dizine çıkabilir. Lab yalnız kendi geçici public/private fixture dosyalarını okur; sistem dosyalarına erişmez.

## Keşif
`probe hello.txt` normal belgeyi getirir. `probe ../private/note.txt` özel eğitim notuna erişiyor mu? Önce tahmin et, sonra iki sonucu karşılaştır. Kanıtı gönder.

```python
candidate = (public / user_path).resolve()
if not candidate.is_relative_to(public.resolve()):
    raise PermissionError('Kök dışı yol')
```

## Neden string öneki yetmez?
`/data/public-evil` metni `/data/public` ile başlar ama o dizinin altında değildir. Path bileşenleriyle karşılaştır. Sembolik bağlantı ve eşzamanlı dosya değişiklikleri ek risklerdir; hassas üretim kodunda descriptor tabanlı açma ve symlink politikası da gerekir.

## Savunma
`patch confine-root` sonrasında özel dosya reddedilmeli, `hello.txt` okunabilmelidir. `verify` iki koşulu birlikte sınar. Her dosyayı reddetmek başarı sayılmaz.

Kontrol sorusu: yalnız `..` metnini silmek yeterli mi? Hayır; kodlama, mutlak yol ve platform farkları nedeniyle çözümlenmiş yol sınırı gerekir.
