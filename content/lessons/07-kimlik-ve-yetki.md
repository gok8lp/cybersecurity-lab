---
slug: kimlik-ve-yetki
module: identity
title: Kimlik doğrulama ve nesne sahipliği
type: theory
minutes: 10
prerequisites:
- http-temelleri
---
# Kimlik doğrulama ve nesne sahipliği

Authentication kim olduğunu, authorization hangi nesneye hangi işlemi yapabileceğini belirler. Kullanıcının oturum açması bütün notlara erişebileceği anlamına gelmez.

## Keşif
`object-ownership` içinde `probe 1` normal öğrenci notunu, `probe 2` başka bir oyuncak kullanıcının kaydını temsil eder. İlk sürüm yalnız nesne kimliğini kontrol eder.

## Düzeltme
Sorguda hem nesne kimliğini hem sunucudan gelen kullanıcı kimliğini filtrele: `WHERE id=? AND owner_id=?`. Tarayıcıdan gelen owner_id güvenilir değildir.

## Regresyon
Başka kullanıcının notu reddedilmeli, kendi notun erişilebilir kalmalı. Kontrol sorusu: bağlantıyı arayüzden gizlemek yeterli mi? Hayır, sunucu kontrolü gerekir.
