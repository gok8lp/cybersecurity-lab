"""Tarayıcıda çözülen bulmacalar (lab gerektirmez). Cevaplar düz metin tutulmaz: sha256(normalize(cevap))."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from pathlib import Path

import yaml

from .content import ICERIK, SLUG


def normalize(metin: str, kural: str = "kucuk-bosluksuz") -> str:
    t = metin.strip()
    if kural == "kucuk-bosluksuz":
        t = "".join(t.split()).lower()
    elif kural == "aynen":
        pass
    return t


def ozet(metin: str, kural: str) -> str:
    return hashlib.sha256(normalize(metin, kural).encode()).hexdigest()


@dataclass(frozen=True)
class Bulmaca:
    slug: str
    kategori: str
    zorluk: str
    baslik: str
    soru: str
    cevap_tipi: str
    secenekler: tuple[str, ...]
    cevap_ozeti: str
    normalize: str
    ipuclari: tuple[str, ...]
    aciklama: str
    xp: int

    def dogru_mu(self, cevap: str) -> bool:
        return hmac.compare_digest(ozet(cevap, self.normalize), self.cevap_ozeti)

    def kamu(self) -> dict:
        # istemciye cevap özeti ve açıklama gönderilmez
        return {"slug": self.slug, "kategori": self.kategori, "zorluk": self.zorluk, "baslik": self.baslik,
                "soru": self.soru, "cevap_tipi": self.cevap_tipi, "secenekler": list(self.secenekler),
                "ipuclari": list(self.ipuclari), "xp": self.xp}


def yukle(yol: Path = ICERIK / "puzzles.yaml") -> dict[str, Bulmaca]:
    if not yol.exists():
        return {}
    sonuc = {}
    for b in yaml.safe_load(yol.read_text(encoding="utf-8")) or []:
        if not SLUG.fullmatch(b["slug"]):
            raise ValueError(f"Geçersiz bulmaca slug: {b['slug']!r}")
        sonuc[b["slug"]] = Bulmaca(slug=b["slug"], kategori=b["kategori"], zorluk=b["zorluk"], baslik=b["baslik_tr"],
                                   soru=b["soru"], cevap_tipi=b["cevap_tipi"], secenekler=tuple(b.get("secenekler", [])),
                                   cevap_ozeti=b["cevap_ozeti"], normalize=b.get("normalize", "kucuk-bosluksuz"),
                                   ipuclari=tuple(b.get("ipuclari", [])), aciklama=b.get("aciklama", ""), xp=int(b["xp"]))
    return sonuc
