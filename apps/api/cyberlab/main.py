"""Siber Güvenlik Laboratuvarı API (FastAPI). Docker'a dokunmaz; laboratuvar işleri runner'a devredilir."""
from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine, select

from . import content, flags, puzzles
from .models import Attempt, LabSession, Progress, User, simdi

class Cevap(BaseModel):
    cevap: str


class OturumIstek(BaseModel):
    challenge: str


class Gonderim(BaseModel):
    flag: str


VERI = Path(os.environ.get("CYBERLAB_DATA", Path(__file__).resolve().parents[3] / "data"))


def _sir() -> bytes:
    yol = VERI / "server_secret"
    if not yol.exists():
        VERI.mkdir(parents=True, exist_ok=True)
        yol.write_bytes(secrets.token_bytes(48))
        yol.chmod(0o600)
    return yol.read_bytes()


def uygulama(db_url: str | None = None, runner=None) -> FastAPI:
    motor = create_engine(db_url or f"sqlite:///{VERI / 'cyberlab.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(motor)
    challengelar = content.challenge_yukle()
    dersler = content.ders_yukle()
    bulmacalar = puzzles.yukle()
    app = FastAPI(title="Siber Güvenlik Laboratuvarı")

    def db():
        with Session(motor) as s:
            yield s

    def kullanici(s: Session = Depends(db)) -> User:
        u = s.exec(select(User)).first()
        if not u:
            u = User()
            s.add(u)
            s.commit()
            s.refresh(u)
        return u

    @app.get("/api/health")
    def saglik():
        return {"durum": "ok"}

    @app.get("/api/health/capacity")
    def kapasite():
        if runner is None:
            return {"uygun": False, "neden": "runner-yok"}
        return runner.kapasite()

    @app.get("/api/challenges")
    def challenge_listesi():
        return [{"slug": c.slug, "module": c.module, "difficulty": c.difficulty, "title": c.title_tr,
                 "type": c.type, "objective": c.objective, "score": c.score} for c in challengelar.values()]

    @app.get("/api/lessons")
    def ders_listesi():
        return [{"slug": d.slug, "module": d.module, "title": d.title, "type": d.type, "minutes": d.minutes,
                 "prerequisites": list(d.prerequisites)} for d in dersler.values()]

    @app.get("/api/lessons/{slug}")
    def ders(slug: str):
        d = dersler.get(slug)
        if not d:
            raise HTTPException(404, "Ders yok")
        return {"slug": d.slug, "title": d.title, "body": d.body, "prerequisites": list(d.prerequisites)}

    @app.get("/api/puzzles")
    def bulmaca_listesi():
        return [p.kamu() for p in bulmacalar.values()]

    @app.post("/api/puzzles/{slug}/answer")
    def bulmaca_cevap(slug: str, c: Cevap, u: User = Depends(kullanici), s: Session = Depends(db)):
        p = bulmacalar.get(slug)
        if not p:
            raise HTTPException(404, "Bulmaca yok")
        dogru = p.dogru_mu(c.cevap)
        if dogru:
            ilerleme = s.exec(select(Progress).where(Progress.user_id == u.id, Progress.slug == f"bulmaca:{slug}")).first()
            if not ilerleme:
                s.add(Progress(user_id=u.id, slug=f"bulmaca:{slug}", status="tamam", completed_at=simdi()))
                u.xp += p.xp
                s.add(u)
                s.commit()
        return {"dogru": dogru, "aciklama": p.aciklama if dogru else None}

    @app.post("/api/sessions")
    def oturum_ac(istek: OturumIstek, u: User = Depends(kullanici), s: Session = Depends(db)):
        if istek.challenge not in challengelar:
            raise HTTPException(404, "Challenge yok")
        oid = secrets.token_hex(6)
        flag = flags.flag_uret(_sir(), u.id, oid, istek.challenge)
        oturum = LabSession(id=oid, user_id=u.id, challenge=istek.challenge, flag_hash=flags.flag_ozeti(flag),
                            expires_at=simdi() + timedelta(minutes=45))
        if runner is None:
            oturum.state = "runner-yok"
        else:
            oturum.state = runner.baslat(istek.challenge, oid, flag).get("durum", "hata")
        s.add(oturum)
        s.commit()
        return {"id": oid, "state": oturum.state}

    @app.post("/api/sessions/{oid}/submit")
    def gonder(oid: str, g: Gonderim, u: User = Depends(kullanici), s: Session = Depends(db)):
        oturum = s.get(LabSession, oid)
        if not oturum or oturum.user_id != u.id:
            raise HTTPException(404, "Oturum yok")
        dogru = flags.flag_dogru(g.flag, oturum.flag_hash)
        if not dogru:
            # başka bir oturumun flag'i mi? (tekrar kullanım engeli: yalnız kendi oturumunda geçerli)
            baska = s.exec(select(LabSession).where(LabSession.flag_hash == flags.flag_ozeti(g.flag))).first()
            sonuc = "baska-oturum" if baska else "yanlis"
        else:
            sonuc = "dogru"
        s.add(Attempt(session_id=oid, result=sonuc))
        s.commit()
        return {"sonuc": sonuc}

    @app.get("/api/progress")
    def ilerleme(u: User = Depends(kullanici), s: Session = Depends(db)):
        kayitlar = s.exec(select(Progress).where(Progress.user_id == u.id)).all()
        return {"xp": u.xp, "tamamlanan": [p.slug for p in kayitlar if p.status == "tamam"]}

    return app


app = uygulama() if os.environ.get("CYBERLAB_AUTO") == "1" else None
