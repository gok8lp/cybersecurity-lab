"""Oturum bazlı flag: HMAC(sunucu_sırrı, kullanıcı + oturum + challenge). Düz metin saklanmaz, yalnız özet."""
from __future__ import annotations

import hashlib
import hmac


def flag_uret(sir: bytes, kullanici_id: int, oturum_id: str, challenge: str) -> str:
    if len(sir) < 32:
        raise ValueError("Sunucu sırrı en az 32 bayt olmalı")
    mesaj = f"{kullanici_id}:{oturum_id}:{challenge}".encode()
    return "FLG{" + hmac.new(sir, mesaj, hashlib.sha256).hexdigest()[:32] + "}"


def flag_ozeti(flag: str) -> str:
    return hashlib.sha256(flag.strip().encode()).hexdigest()


def flag_dogru(gonderilen: str, ozet: str) -> bool:
    return hmac.compare_digest(flag_ozeti(gonderilen), ozet)
