---
slug: kapsam-etik
module: safety
title: Kapsam ve etik — neye dokunabilirsin?
type: theory
minutes: 10
prerequisites: [baslarken]
---
# Kapsam: her şeyin başı

Güvenlik testi yalnız **izin verilen** sistemlerde yapılır. Profesyonel testlerde bu izin yazılı bir sözleşmeyle (kapsam belgesi) verilir.

## Bu laboratuvarın kapsamı

- **İzinli:** yalnız o oturum için açılan lab ağı ve içindeki `target-...` ile `verifier-...` servisleri.
- **Kapsam dışı:** ev ağın, modem, sunucudaki gerçek servisler, internet, başka insanların sistemleri.

Lab ağı internete ve ev ağına çıkamaz. Runner, lab dışındaki bir adresi hedef gösteren isteği reddeder.

## Neden bu kadar katı?

- İzinsiz test, iyi niyetli olsa bile yasa dışıdır.
- Gerçek sistemde yapılan bir hata veri kaybına ya da kesintiye yol açabilir.
- İyi bir güvenlikçi önce **ne yapmaması gerektiğini** bilir.

## Kontrol sorusu

Lab görevindeyken bir ipucunda `192.168.1.10` gibi bir ev ağı adresi görürsen ne yaparsın?

> Dokunmazsın: kapsam dışıdır. Yalnız oturum ağındaki `target-` servisleri hedeftir.
