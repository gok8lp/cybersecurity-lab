---
slug: parola-saklama
module: identity
title: 'Parolalar: salt ve pahalı doğrulama'
type: theory
minutes: 12
prerequisites:
- kimlik-ve-yetki
challenge: password-storage
introduced: '1.1'
---
# Parolalar: salt ve pahalı doğrulama

Kriptografik hash tek yönlü olabilir ama parolayı kendiliğinden korumaz. Parolalar düşük entropili olduğunda adaylar hashlenip karşılaştırılabilir. SHA-256 gibi hızlı fonksiyonlar bu denemeyi ucuzlatır.

## Kontrollü deney
`probe` yalnız üç kelimelik sabit bir eğitim sözlüğünü saltsız SHA-256 özetiyle karşılaştırır. Gerçek parola veya harici sistem kullanılmaz. Eşleşmenin bulunması eğitim kanıtını verir.

## Salt ne sağlar?
Aynı parola için farklı salt farklı sonuç verir; hesaplar arasında ön hesaplamayı paylaşmayı zorlaştırır. Salt gizli değildir. `patch salted-scrypt` her kayıt için `os.urandom(16)` kullanır.

```python
hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
```

## Doğrulama
`verify` iki ayrı saltın farklı özetler verdiğini, doğru parolanın eşleştiğini ve yanlış parolanın reddedildiğini kontrol eder. Karşılaştırma `hmac.compare_digest` ile yapılır.

Lab parametreleri kaynak bütçesine göre sabittir; üretimde maliyeti ölçmek, güncel parola saklama rehberlerine göre ayarlamak ve maliyet yükseltme planı gerekir. scrypt zayıf bir parolayı tahmin edilemez yapmaz. Rate limit ve güçlü parola politikası ayrı katmanlardır.

Kontrol sorusu: saltı her kullanıcı için aynı sabit metin yapmak aynı faydayı sağlar mı? Hayır.
