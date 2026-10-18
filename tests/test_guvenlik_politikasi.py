"""Compose güvenlik politikası: ihlal varsa test (ve CI) başarısız olur."""
from pathlib import Path

import pytest
import yaml

KOK = Path(__file__).resolve().parents[1]
LAB_DOSYALARI = sorted((KOK / "labs").glob("*/compose.yaml"))
TUM = LAB_DOSYALARI + [p for p in [KOK / "docker-compose.yml"] if p.exists()]


def servisler(yol):
    return (yaml.safe_load(yol.read_text()) or {}).get("services", {}).items()


@pytest.mark.parametrize("yol", TUM, ids=lambda p: str(p.relative_to(KOK)))
def test_yasakli_ayarlar_yok(yol):
    for ad, s in servisler(yol):
        assert not s.get("privileged"), f"{ad}: privileged yasak"
        for anahtar in ("network_mode", "pid", "ipc", "userns_mode", "uts"):
            assert s.get(anahtar) != "host", f"{ad}: {anahtar}: host yasak"
        assert not s.get("devices"), f"{ad}: aygıt bağlamak yasak"
        for v in s.get("volumes", []) or []:
            metin = v if isinstance(v, str) else str(v.get("source", ""))
            assert "docker.sock" not in metin, f"{ad}: docker.sock yasak"
            kaynak = metin.split(":")[0] if isinstance(v, str) else metin
            assert not kaynak.startswith(("/", "~", "..")), f"{ad}: host dizini bağlamak yasak ({kaynak})"
        caps = s.get("cap_add") or []
        assert set(caps) <= {"NET_RAW"}, f"{ad}: izinsiz yetki {caps}"
        for p in s.get("ports", []) or []:
            assert str(p).startswith("127.0.0.1:"), f"{ad}: port yalnız 127.0.0.1'e bağlanabilir ({p})"


@pytest.mark.parametrize("yol", LAB_DOSYALARI, ids=lambda p: p.parent.name)
def test_lab_sertlestirme(yol):
    belge = yaml.safe_load(yol.read_text())
    for ad, s in belge["services"].items():
        assert s.get("read_only") is True, f"{ad}: salt-okunur kök zorunlu"
        assert s.get("cap_drop") == ["ALL"], f"{ad}: cap_drop ALL zorunlu"
        assert "no-new-privileges:true" in (s.get("security_opt") or []), f"{ad}: no-new-privileges zorunlu"
        assert s.get("mem_limit") and s.get("pids_limit") and s.get("cpus"), f"{ad}: kaynak sınırı zorunlu"
        assert s.get("healthcheck"), f"{ad}: sağlık kontrolü zorunlu"
        assert s.get("labels", {}).get("com.flugel.cyberlab.managed") == "true", f"{ad}: managed etiketi zorunlu"
        assert not s.get("ports"), f"{ad}: lab hedefi port yayımlayamaz"
    for ad, ag in belge.get("networks", {}).items():
        assert ag.get("internal") is True, f"ağ {ad}: internal:true zorunlu"


def test_haftalik_gorev_dizinleri_kapsam_disi():
    for yol in KOK.rglob("*"):
        if ".venv" in yol.parts or "node_modules" in yol.parts or yol.is_dir() or yol.suffix in {".png", ".db", ".md"}:
            continue
        if yol.name == "test_guvenlik_politikasi.py":
            continue
        metin = yol.read_text(errors="ignore")
        assert "weekly-task" not in metin, f"{yol}: weekly-task kapsamına girilmez"
