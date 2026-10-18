---
slug: linux-izinleri
module: linux
title: Linux dosya izinleri — kim neyi okuyabilir?
type: theory
minutes: 12
prerequisites: [kapsam-etik]
---
# Linux izinleri

`ls -l` çıktısının başındaki on karakter dosyanın türünü ve izinlerini gösterir:

    -rw-r--r--  1 app app  512 yedek.tar

- 1. karakter: tür (`-` dosya, `d` dizin).
- Sonraki üçlüler: **sahip**, **grup**, **diğerleri** için okuma (`r`), yazma (`w`), çalıştırma (`x`).

Yukarıdaki dosyayı sistemdeki **herkes okuyabilir** (`r--` diğerleri).

## Sayısal gösterim

`r=4`, `w=2`, `x=1`. Üçlüler toplanır:

| İzin | Sayı | Anlamı |
|---|---|---|
| `rw-------` | 600 | yalnız sahip okur/yazar |
| `rw-r-----` | 640 | sahip okur/yazar, grup okur |
| `rw-r--r--` | 644 | herkes okur |

## En az yetki ilkesi

Bir dosya yalnız ihtiyacı olanlar tarafından okunabilmelidir. Yedekler, anahtarlar ve yapılandırmalar çoğunlukla `600` ya da `640` olmalıdır.

    chmod 600 yedek.tar
    chown app:app yedek.tar

## Bu modülün lab görevi

**Fazla izinli yedek:** bir serviste herkesin okuyabildiği bir yedek dosyası var. Önce bu yüzden sızan flag'i bulacaksın, sonra izni düzelteceksin. Doğrulayıcı, servisin hâlâ çalıştığını ve yetkisiz okumanın başarısız olduğunu kontrol eder.
