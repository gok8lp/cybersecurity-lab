import yaml
from fastapi.testclient import TestClient
from pathlib import Path

from cyberlab.main import uygulama

KOK = Path(__file__).resolve().parents[1]


class SahteRunner:
    def __init__(self):
        self.flaglar = {}

    def kapasite(self):
        return {"uygun": True, "neden": None, "bellek_gb": 5, "yuk": "normal"}

    def baslat(self, slug, oid, flag):
        self.flaglar[oid] = flag
        return {"durum": "saglikli"}


def istemci(tmp_path, monkeypatch):
    monkeypatch.setenv("CYBERLAB_DATA", str(tmp_path))
    import cyberlab.main as m
    m.VERI = tmp_path
    r = SahteRunner()
    return TestClient(uygulama(f"sqlite:///{tmp_path / 't.db'}", runner=r)), r


def test_saglik_ve_icerik(tmp_path, monkeypatch):
    c, _ = istemci(tmp_path, monkeypatch)
    assert c.get("/api/health").json() == {"durum": "ok"}
    assert any(x["slug"] == "linux-permission-leak" for x in c.get("/api/challenges").json())
    assert c.get("/api/lessons/baslarken").status_code == 200
    bulmacalar = c.get("/api/puzzles").json()
    assert len(bulmacalar) >= 12
    assert all("cevap_ozeti" not in b and "aciklama" not in b for b in bulmacalar)


def test_flag_yalniz_kendi_oturumunda(tmp_path, monkeypatch):
    c, r = istemci(tmp_path, monkeypatch)
    a = c.post("/api/sessions", json={"challenge": "linux-permission-leak"}).json()
    b = c.post("/api/sessions", json={"challenge": "linux-permission-leak"}).json()
    assert a["state"] == "saglikli" and a["id"] != b["id"]
    assert c.post(f"/api/sessions/{a['id']}/submit", json={"flag": r.flaglar[a["id"]]}).json()["sonuc"] == "dogru"
    assert c.post(f"/api/sessions/{b['id']}/submit", json={"flag": r.flaglar[a["id"]]}).json()["sonuc"] == "baska-oturum"
    assert c.post(f"/api/sessions/{a['id']}/submit", json={"flag": "FLG{yanlis}"}).json()["sonuc"] == "yanlis"
    assert c.post("/api/sessions", json={"challenge": "olmayan"}).status_code == 404


def test_bulmaca_cevaplari_ve_xp(tmp_path, monkeypatch):
    c, _ = istemci(tmp_path, monkeypatch)
    kaynak = yaml.safe_load((KOK / "tests" / "bulmaca_kaynak.yaml").read_text())
    for b in kaynak:
        yanit = c.post(f"/api/puzzles/{b['slug']}/answer", json={"cevap": str(b["cevap"])}).json()
        assert yanit["dogru"], b["slug"]
        assert yanit["aciklama"]
    assert not c.post("/api/puzzles/b64-coz/answer", json={"cevap": "yanlis"}).json()["dogru"]
    # aynı bulmaca iki kez XP vermez
    xp = c.get("/api/progress").json()["xp"]
    c.post("/api/puzzles/b64-coz/answer", json={"cevap": "cyber range"})
    assert c.get("/api/progress").json()["xp"] == xp == sum(b["xp"] for b in kaynak)
