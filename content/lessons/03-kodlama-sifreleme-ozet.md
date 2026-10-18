---
slug: kodlama-sifreleme-ozet
module: crypto
title: Kodlama, şifreleme ve özet farkı
type: theory
minutes: 12
prerequisites: [baslarken]
---
# Üç farklı şey

| | Amaç | Geri çevrilir mi? | Örnek |
|---|---|---|---|
| **Kodlama** | Veriyi taşınabilir biçime çevirmek | Evet, anahtarsız | Base64, hex, URL kodlama |
| **Şifreleme** | Gizlilik | Evet, yalnız anahtarla | AES, ChaCha20 |
| **Özet (hash)** | Bütünlük, parola saklama | Hayır | SHA-256, bcrypt |

## Sık yapılan hata

"Parolayı base64 ile sakladım" demek, parolayı **açık** saklamak demektir: base64 herkes tarafından çözülebilir.

## Parola saklama

Parolalar şifrelenmez, **yavaş ve tuzlu** bir özetle saklanır (bcrypt, scrypt, Argon2). MD5 ve SHA-1 parola için uygun değildir: çok hızlıdırlar ve hazır tablolarla eşleşebilirler.

## Özet uzunlukları (onaltılık)

- MD5: 32 hane
- SHA-1: 40 hane
- SHA-256: 64 hane

Bulmacalar bölümünde bu üçünü ayırt etmeyi deneyeceksin.
