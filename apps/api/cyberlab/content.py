"""İçerik yükleyici: challenges.yaml + lessons/*.md (ön bilgi bloğu). Önkoşul döngüsü tespit edilir."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

KOK = Path(__file__).resolve().parents[3]
ICERIK = KOK / "content"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


@dataclass(frozen=True)
class Challenge:
    slug: str
    module: str
    difficulty: str
    title_tr: str
    type: str
    objective: str
    score: int
    raw: dict = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class Lesson:
    slug: str
    module: str
    title: str
    type: str
    minutes: int
    prerequisites: tuple[str, ...]
    body: str


def challenge_yukle(yol: Path = ICERIK / "challenges.yaml") -> dict[str, Challenge]:
    veri = yaml.safe_load(yol.read_text(encoding="utf-8"))
    sonuc: dict[str, Challenge] = {}
    for c in veri.get("challenges", []):
        slug = c["slug"]
        if not SLUG.fullmatch(slug):
            raise ValueError(f"Geçersiz challenge slug: {slug!r}")
        if slug in sonuc:
            raise ValueError(f"Yinelenen challenge: {slug}")
        sonuc[slug] = Challenge(slug=slug, module=c["module"], difficulty=c["difficulty"], title_tr=c["title_tr"],
                                type=c["type"], objective=c["objective"], score=int(c["score"]), raw=c)
    return sonuc


def _on_bilgi(metin: str) -> tuple[dict, str]:
    if not metin.startswith("---\n"):
        raise ValueError("Ders dosyası '---' ön bilgi bloğuyla başlamalı")
    _, bas, govde = metin.split("---\n", 2)
    return yaml.safe_load(bas) or {}, govde.strip()


def ders_yukle(klasor: Path = ICERIK / "lessons") -> dict[str, Lesson]:
    dersler: dict[str, Lesson] = {}
    for yol in sorted(klasor.glob("*.md")):
        on, govde = _on_bilgi(yol.read_text(encoding="utf-8"))
        slug = on["slug"]
        if not SLUG.fullmatch(slug):
            raise ValueError(f"Geçersiz ders slug: {slug!r}")
        if slug in dersler:
            raise ValueError(f"Yinelenen ders: {slug}")
        dersler[slug] = Lesson(slug=slug, module=on["module"], title=on["title"], type=on["type"],
                               minutes=int(on.get("minutes", 10)), prerequisites=tuple(on.get("prerequisites", [])),
                               body=govde)
    dongu_denetle(dersler)
    return dersler


def dongu_denetle(dersler: dict[str, Lesson]) -> None:
    """Önkoşul grafiğinde bilinmeyen ders ya da döngü varsa ValueError."""
    for d in dersler.values():
        for p in d.prerequisites:
            if p not in dersler:
                raise ValueError(f"{d.slug}: bilinmeyen önkoşul {p}")
    durum: dict[str, int] = {}

    def gez(slug: str, yol: list[str]) -> None:
        if durum.get(slug) == 2:
            return
        if durum.get(slug) == 1:
            raise ValueError("Önkoşul döngüsü: " + " -> ".join([*yol, slug]))
        durum[slug] = 1
        for p in dersler[slug].prerequisites:
            gez(p, [*yol, slug])
        durum[slug] = 2

    for s in dersler:
        gez(s, [])
