"""Release API: single owner, loopback only, private runner broker."""
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select
from . import content, flags, puzzles
from .models import Activity, Attempt, Audit, Hint, LabSession, Progress, User, simdi

WRITE = threading.RLock()
class Cevap(BaseModel):
    cevap: str = Field(min_length=1, max_length=2048)
class OturumIstek(BaseModel):
    challenge: str = Field(min_length=2, max_length=63)
class Gonderim(BaseModel):
    flag: str = Field(min_length=1, max_length=256)
class Komut(BaseModel):
    command: str = Field(min_length=1, max_length=512)
def aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

def uygulama(db_url=None, runner=None):
    data = Path(os.getenv('CYBERLAB_DATA', content.KOK / 'data'))
    data.mkdir(parents=True, exist_ok=True)
    secret_path = data / 'server_secret'
    try:
        with secret_path.open('xb') as f:
            secret_path.chmod(0o600)
            f.write(secrets.token_bytes(48))
    except FileExistsError:
        pass
    secret = secret_path.read_bytes()
    engine = create_engine(db_url or f'sqlite:///{data / "cyberlab.db"}', connect_args={'check_same_thread': False, 'timeout': 30})
    @event.listens_for(engine, 'connect')
    def pragma(connection, _):
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA foreign_keys=ON')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if not s.get(User, 1):
            s.add(User(id=1)); s.commit()
    challenges, lessons, ps = content.challenge_yukle(), content.ders_yukle(), puzzles.yukle()
    app = FastAPI(title='FLUGEL Cyber Range', version='1.0.0', docs_url='/api/docs', redoc_url=None)
    app.state.engine = engine
    limits = defaultdict(deque)
    hosts = set(os.getenv('CYBERLAB_HOSTS', '127.0.0.1,localhost,testserver').split(','))
    @app.middleware('http')
    async def boundary(request: Request, call_next):
        host = request.headers.get('host', '')
        if urlsplit('http://' + host).hostname not in hosts:
            return JSONResponse({'detail': 'İzin verilmeyen Host'}, status_code=400)
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            origin = request.headers.get('origin')
            if (origin and urlsplit(origin).netloc != host) or request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': 'Farklı kaynaktan istek reddedildi'}, status_code=403)
            if 'application/json' not in request.headers.get('content-type', ''):
                return JSONResponse({'detail': 'JSON gerekli'}, status_code=415)
            size = request.headers.get('content-length', '0')
            if not size.isdigit() or int(size) > 8192:
                return JSONResponse({'detail': 'İstek çok büyük'}, status_code=413)
            key = request.client.host if request.client else 'local'
            now = time.monotonic(); bucket = limits[key]
            while bucket and bucket[0] < now-60:
                bucket.popleft()
            if len(bucket) >= 120:
                return JSONResponse({'detail': 'Çok fazla deneme; bir dakika bekle'}, status_code=429, headers={'Retry-After': '60'})
            bucket.append(now)
        response = await call_next(request)
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
            'Cache-Control': 'no-store' if request.url.path.startswith('/api') else 'no-cache',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"})
        return response
    def db():
        with Session(engine) as s:
            yield s
    def audit(s, action, subject, result):
        s.add(Audit(action=action, subject=subject, result=result))
    def progress(s, slug):
        return s.exec(select(Progress).where(Progress.user_id == 1, Progress.slug == slug)).first()
    def award(s, slug, xp):
        if progress(s, slug): return 0
        s.add(Progress(user_id=1, slug=slug, status='tamam', completed_at=simdi()))
        user = s.get(User, 1); user.xp += xp; s.add(user)
        day = simdi().astimezone(timezone(timedelta(hours=3))).date().isoformat()
        if not s.exec(select(Activity).where(Activity.user_id == 1, Activity.day == day)).first():
            s.add(Activity(user_id=1, day=day))
        return xp
    def lab_get(s, oid, active=False):
        lab = s.get(LabSession, oid)
        if not lab or lab.user_id != 1: raise HTTPException(404, 'Oturum yok')
        if active and (aware(lab.expires_at) <= simdi() or lab.state not in {'saglikli', 'saldiri-tamam'}):
            raise HTTPException(409, 'Oturum etkin değil; yeni lab başlat')
        return lab
    def public(lab):
        state = 'suresi-doldu' if lab.state in {'saglikli', 'saldiri-tamam'} and aware(lab.expires_at) <= simdi() else lab.state
        return {'id': lab.id, 'challenge': lab.challenge, 'state': state, 'expires_at': aware(lab.expires_at).isoformat()}
    @app.get('/api/health')
    def health(): return {'durum': 'ok'}
    @app.get('/api/health/capacity')
    def capacity(): return runner.kapasite() if runner else {'uygun': False, 'neden': 'runner-yok'}
    @app.get('/api/challenges')
    def challenge_list():
        return [{'slug': c.slug, 'module': c.module, 'difficulty': c.difficulty, 'title': c.title_tr, 'type': c.type,
                 'objective': c.objective, 'score': c.score, 'guide': c.raw.get('guide', ''), 'prerequisites': c.raw.get('prerequisites', [])} for c in challenges.values()]
    @app.get('/api/lessons')
    def lesson_list():
        return [{'slug': d.slug, 'module': d.module, 'title': d.title, 'type': d.type, 'minutes': d.minutes, 'prerequisites': list(d.prerequisites)} for d in lessons.values()]
    @app.get('/api/lessons/{slug}')
    def lesson(slug: str):
        d = lessons.get(slug)
        if not d: raise HTTPException(404, 'Ders yok')
        return {'slug': d.slug, 'title': d.title, 'body': d.body, 'prerequisites': list(d.prerequisites)}
    @app.post('/api/lessons/{slug}/complete')
    def complete(slug: str, s: Session = Depends(db)):
        if slug not in lessons: raise HTTPException(404, 'Ders yok')
        with WRITE:
            if any(not progress(s, 'ders:'+p) for p in lessons[slug].prerequisites):
                raise HTTPException(409, 'Önce önkoşul derslerini tamamla')
            xp = award(s, 'ders:'+slug, 50); audit(s, 'lesson', slug, 'tamam'); s.commit()
        return {'xp': xp}
    @app.get('/api/puzzles')
    def puzzle_list(s: Session = Depends(db)):
        results = []
        for p in ps.values():
            row = p.kamu(); h = s.exec(select(Hint).where(Hint.user_id == 1, Hint.slug == p.slug)).first()
            row.update(ipucu_sayisi=len(p.ipuclari), ipuclari=list(p.ipuclari[:h.count if h else 0])); results.append(row)
        return results
    @app.post('/api/puzzles/{slug}/hint')
    def hint(slug: str, s: Session = Depends(db)):
        if slug not in ps: raise HTTPException(404, 'Bulmaca yok')
        with WRITE:
            h = s.exec(select(Hint).where(Hint.user_id == 1, Hint.slug == slug)).first() or Hint(user_id=1, slug=slug)
            h.count = min(h.count+1, len(ps[slug].ipuclari)); s.add(h); audit(s, 'hint', slug, str(h.count)); s.commit()
        return {'ipuclari': list(ps[slug].ipuclari[:h.count])}
    @app.post('/api/puzzles/{slug}/answer')
    def answer(slug: str, c: Cevap, s: Session = Depends(db)):
        p = ps.get(slug)
        if not p: raise HTTPException(404, 'Bulmaca yok')
        correct, xp = p.dogru_mu(c.cevap), 0
        with WRITE:
            if correct:
                h = s.exec(select(Hint).where(Hint.user_id == 1, Hint.slug == slug)).first()
                factor = .75 if h and h.count >= 3 else .9 if h and h.count >= 2 else 1
                xp = award(s, 'bulmaca:'+slug, int(p.xp*factor))
            audit(s, 'answer', slug, 'dogru' if correct else 'yanlis'); s.commit()
        return {'dogru': correct, 'aciklama': p.aciklama if correct else None, 'xp': xp}
    @app.get('/api/sessions')
    def sessions(s: Session = Depends(db)):
        return [public(x) for x in s.exec(select(LabSession).where(LabSession.user_id == 1).order_by(LabSession.started_at.desc()).limit(30)).all()]
    @app.get('/api/sessions/{oid}')
    def session_detail(oid: str, s: Session = Depends(db)): return public(lab_get(s, oid))
    @app.post('/api/sessions')
    def start(req: OturumIstek, s: Session = Depends(db)):
        c = challenges.get(req.challenge)
        if not c: raise HTTPException(404, 'Challenge yok')
        with WRITE:
            if any(not progress(s, 'lab:'+p) for p in c.raw.get('prerequisites', [])):
                raise HTTPException(409, 'Önce gerekli labları savunma adımıyla tamamla')
            active = [x for x in s.exec(select(LabSession)).all() if x.state in {'saglikli','saldiri-tamam'} and aware(x.expires_at)>simdi()]
            if len(active)>=2: raise HTTPException(409, 'En fazla iki etkin lab; önce birini durdur')
            oid = secrets.token_hex(6); flag = flags.flag_uret(secret, 1, oid, req.challenge)
            lab = LabSession(id=oid, user_id=1, challenge=req.challenge, flag_hash=flags.flag_ozeti(flag), expires_at=simdi()+timedelta(minutes=45))
            try: result = runner.baslat(req.challenge, oid, flag) if runner else {'durum':'runner-yok'}
            except RuntimeError: raise HTTPException(503, 'Lab servisine erişilemiyor')
            lab.state = result.get('durum','hata'); s.add(lab); audit(s,'start',oid,lab.state); s.commit()
            return {**public(lab), 'neden':result.get('neden')}
    @app.post('/api/sessions/{oid}/stop')
    def stop(oid: str, s: Session = Depends(db)):
        with WRITE:
            lab = lab_get(s, oid)
            try: result = runner.durdur(lab.challenge,oid) if runner else {'durum':'bitti'}
            except RuntimeError: raise HTTPException(503,'Lab durdurulamadı')
            if result.get('durum')!='bitti': raise HTTPException(503,'Lab durdurulamadı')
            lab.state='bitti'; s.add(lab); audit(s,'stop',oid,'bitti'); s.commit()
        return public(lab)
    @app.post('/api/sessions/{oid}/command')
    def command(oid: str, req: Komut, s: Session = Depends(db)):
        lab=lab_get(s,oid,True)
        if not runner: raise HTTPException(503,'Runner yok')
        try: result=runner.komut(lab.challenge,oid,req.command)
        except RuntimeError: raise HTTPException(503,'Komut çalıştırılamadı')
        audit(s,'command',oid,'ok'); s.commit(); return result
    @app.post('/api/sessions/{oid}/submit')
    def submit(oid: str,g: Gonderim,s: Session=Depends(db)):
        with WRITE:
            lab=lab_get(s,oid,True); correct=flags.flag_dogru(g.flag,lab.flag_hash)
            other=s.exec(select(LabSession).where(LabSession.flag_hash==flags.flag_ozeti(g.flag))).first() if not correct else None
            result='dogru' if correct else 'baska-oturum' if other else 'yanlis'
            if correct: lab.state='saldiri-tamam'; s.add(lab)
            s.add(Attempt(session_id=oid,result=result)); audit(s,'submit',oid,result); s.commit()
        return {'sonuc':result}
    @app.post('/api/sessions/{oid}/verify')
    def verify(oid: str,s: Session=Depends(db)):
        with WRITE:
            lab=lab_get(s,oid,True)
            if lab.state!='saldiri-tamam': raise HTTPException(409,'Önce bu oturumun flag değerini doğrula')
            try:
                result=runner.dogrula(lab.challenge,oid)
                if result.get('basarili') and runner.durdur(lab.challenge,oid).get('durum')!='bitti':
                    raise RuntimeError('cleanup')
            except RuntimeError: raise HTTPException(503,'Doğrulama/temizlik başarısız; yeniden dene')
            xp=0
            if result.get('basarili'):
                xp=award(s,'lab:'+lab.challenge,challenges[lab.challenge].score); lab.state='bitti'; s.add(lab)
            audit(s,'verify',oid,str(bool(result.get('basarili')))); s.commit(); return {**result,'xp':xp}
    @app.get('/api/progress')
    def learning_progress(s: Session=Depends(db)):
        rows=s.exec(select(Progress).where(Progress.user_id==1)).all()
        days={x.day for x in s.exec(select(Activity).where(Activity.user_id==1)).all()}
        today=simdi().astimezone(timezone(timedelta(hours=3))).date()
        streak,day=0,today if today.isoformat() in days else today-timedelta(days=1)
        while day.isoformat() in days: streak+=1; day-=timedelta(days=1)
        xp=s.get(User,1).xp
        return {'xp':xp,'tamamlanan':[x.slug for x in rows],'streak':streak,'level':1+xp//500,
                'review':[{'slug':p.slug,'days':n} for p in rows if p.completed_at for n in (1,7,30) if aware(p.completed_at).date()+timedelta(days=n)==today]}
    @app.get('/api/events')
    def events(s: Session=Depends(db)): return s.exec(select(Audit).order_by(Audit.id.desc()).limit(30)).all()
    static=Path(os.getenv('CYBERLAB_STATIC',content.KOK/'apps/web/dist'))
    if static.is_dir(): app.mount('/',StaticFiles(directory=static,html=True),name='web')
    return app

def create_app():
    socket=os.getenv('CYBERLAB_RUNNER_SOCKET')
    if socket:
        from .broker import Broker
        return uygulama(runner=Broker(socket))
    return uygulama()
