"""Dar lab broker'ı: yalnız manifest izin listesindeki challenge'ları başlatır/durdurur.

- Shell string yok; docker compose argv ile çağrılır.
- Proje adı cyberlab-<oturum>; tüm kaynaklar com.flugel.cyberlab.managed=true etiketi taşır (compose dosyasında).
- Kapasite eşiği sağlanmazsa başlatmaz.
- Web/API Docker soketini görmez; yalnız bu broker'ın Unix soketiyle konuşur."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from . import kapasite

KOK = Path(__file__).resolve().parents[1]
LABS = KOK / "labs"
OTURUM = re.compile(r"^[a-f0-9]{12}$")


def izin_listesi() -> set[str]:
    veri = yaml.safe_load((KOK / "content" / "challenges.yaml").read_text(encoding="utf-8"))
    tanimli = {c["slug"] for c in veri.get("challenges", [])}
    # yalnız tanımlı VE lab compose dosyası olan challenge'lar başlatılabilir
    return {s for s in tanimli if (LABS / s / "compose.yaml").is_file()}


def _argv(slug: str, oturum: str, eylem: list[str]) -> list[str]:
    if slug not in izin_listesi():
        raise PermissionError(f"İzin listesinde değil: {slug}")
    if not OTURUM.fullmatch(oturum):
        raise ValueError("Geçersiz oturum kimliği")
    return ["docker", "compose", "-p", f"cyberlab-{oturum}", "-f", str(LABS / slug / "compose.yaml"), *eylem]


def baslat_argv(slug: str, oturum: str) -> list[str]:
    return _argv(slug, oturum, ["up", "-d", "--wait", "--wait-timeout", "120"])


def durdur_argv(slug: str, oturum: str) -> list[str]:
    return _argv(slug, oturum, ["down", "--volumes", "--remove-orphans", "--timeout", "10"])


def baslat(slug: str, oturum: str, flag: str) -> dict:
    k = kapasite.simdi()
    if not k.uygun:
        return {"durum": "kuyrukta", "neden": k.neden}
    argv = baslat_argv(slug, oturum)
    sonuc = subprocess.run(argv, env={"PATH": "/usr/bin:/bin", "CYBERLAB_FLAG": flag}, capture_output=True,
                           text=True, timeout=180, check=False)
    return {"durum": "saglikli" if sonuc.returncode == 0 else "hata"}


def durdur(slug: str, oturum: str) -> dict:
    sonuc = subprocess.run(durdur_argv(slug, oturum), env={"PATH": "/usr/bin:/bin"}, capture_output=True,
                           text=True, timeout=60, check=False)
    return {"durum": "bitti" if sonuc.returncode == 0 else "hata"}
