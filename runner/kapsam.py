"""Kapsam koruması: lab dışındaki her hedef reddedilir.

İzinli yalnız oturuma atanmış lab alt ağı (runner'ın oluşturduğu internal ağ) ve lab servis adlarıdır.
Ev LAN'ı, Docker köprüleri, Tailscale/CGNAT, loopback, link-local ve genel internet adresleri reddedilir."""
from __future__ import annotations

import ipaddress
import re

# Lab oturum ağları bu blokta açılır (compose ipam); başka hiçbir özel ağ hedef olamaz.
LAB_BLOK = ipaddress.ip_network("10.213.0.0/16")
SERVIS_ADI = re.compile(r"^(target|verifier)-[a-z0-9-]{1,40}$")


def hedef_izinli(hedef: str, oturum_agi: str | None = None) -> bool:
    hedef = hedef.strip().lower()
    if SERVIS_ADI.fullmatch(hedef):
        return True
    try:
        ip = ipaddress.ip_address(hedef)
    except ValueError:
        return False  # alan adları (dış dünya) kabul edilmez
    if oturum_agi is not None:
        ag = ipaddress.ip_network(oturum_agi)
        if not ag.subnet_of(LAB_BLOK):
            return False
        return ip in ag
    return ip in LAB_BLOK
