---
slug: ag-ve-kapsam
module: network
title: 'Ağ sınırı: IP, port ve servis'
type: theory
minutes: 10
prerequisites:
- kapsam-etik
---
# Ağ sınırı: IP, port ve servis

Bir IP makineyi, port o makinedeki dinleyiciyi belirtir. TCP bağlantısı SYN, SYN/ACK ve ACK ile kurulur. TLS bağlantıyı şifreler; uygulamanın yetkilendirme hatasını düzeltmez.

## Keşif
`service-map` labında yalnız sağlanan servis haritasını incele. Debug servisi gereksiz bilgi verirken health servisi normal işlevi temsil eder. Gerçek LAN adreslerine paket gönderilmez.

## Savunma
Gereksiz servisi kapat; health erişimini koru. Her şeyi kapatmak güvenli bir düzeltme değildir. `scope-guard` görevi de reddetme ve normal hedefi kabul etme koşullarını birlikte öğretir.

## Kontrol sorusu
443 portunun açık olması uygulamanın yetki kontrolünün doğru olduğunu kanıtlar mı? Hayır: port erişimi ile nesne yetkisi farklı katmanlardır.
