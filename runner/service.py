"""Private Unix socket broker. Never accepts a host path, shell, URL or Docker argv."""
import json
import ipaddress
import os
import re
import shlex
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from . import kapasite, runner

ROOT=Path(os.getenv('CYBERLAB_RUNNER_DATA',runner.KOK/'runner/run'))
LOCK=threading.RLock()
SERVICE='target'
COMMANDS={'help','files','read','probe','patch','verify','report'}

class Job(BaseModel):
    slug: str = Field(default='',max_length=63)
    oid: str = Field(default='',max_length=12)
    flag: str = Field(default='',max_length=256)
    command: str = Field(default='',max_length=512)

def load():
    path=ROOT/'sessions.json'
    return json.loads(path.read_text()) if path.exists() else {}

def save(rows):
    ROOT.mkdir(parents=True,exist_ok=True)
    tmp=ROOT/'sessions.tmp'; tmp.write_text(json.dumps(rows)); tmp.chmod(0o600); tmp.replace(ROOT/'sessions.json')

def run(argv, timeout=25, env=None):
    try:
        p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,env=env)
        return p.returncode,(p.stdout+p.stderr)[-16384:]
    except subprocess.TimeoutExpired:
        return 124,'İşlem süre sınırını aştı'

def validate(job):
    if job.slug not in runner.izin_listesi() or not runner.OTURUM.fullmatch(job.oid):
        raise HTTPException(400,'Geçersiz lab/oturum')

def stop_job(slug,oid):
    code,_=run(runner.durdur_argv(slug,oid),timeout=60)
    return code==0

def allocate_subnet(rows):
    """Explicit /28 pool avoids exhausted Docker default pools; never modify existing networks."""
    used=[]
    code,ids=run(['docker','network','ls','--format','{{.ID}}'])
    if code: raise RuntimeError('network inventory unavailable')
    if ids.split():
        code,subnets=run(['docker','network','inspect','--format','{{range .IPAM.Config}}{{println .Subnet}}{{end}}',*ids.split()])
        if code: raise RuntimeError('network inventory unavailable')
        for value in subnets.split():
            try: used.append(ipaddress.ip_network(value,strict=False))
            except ValueError: pass
    code,routes=run(['ip','-j','route','show'])
    if code: raise RuntimeError('route inventory unavailable')
    for route in json.loads(routes):
        if route.get('dst') and route['dst']!='default':
            used.append(ipaddress.ip_network(route['dst'],strict=False))
    used.extend(ipaddress.ip_network(row['subnet']) for row in rows.values() if row.get('subnet'))
    for subnet in ipaddress.ip_network('10.213.0.0/16').subnets(new_prefix=28):
        if all(not subnet.overlaps(other) for other in used if other.version==4): return str(subnet)
    raise RuntimeError('lab network pool exhausted')

def cleanup():
    with LOCK:
        rows=load()
        for oid,row in list(rows.items()):
            if row['expires']<=time.time() and stop_job(row['slug'],oid):
                del rows[oid]
        save(rows)

def reaper(stop):
    while not stop.wait(15):
        try: cleanup()
        except (OSError,ValueError): pass  # retain registry and retry; never remove unrelated Docker resources

@asynccontextmanager
async def lifespan(app):
    ROOT.mkdir(parents=True,exist_ok=True)
    cleanup()
    stop=threading.Event(); thread=threading.Thread(target=reaper,args=(stop,),daemon=True); thread.start()
    yield
    stop.set(); thread.join(timeout=2)

app=FastAPI(docs_url=None,redoc_url=None,lifespan=lifespan)

@app.post('/capacity')
def capacity():
    k=kapasite.simdi().ozet()
    with LOCK:
        if len(load())>=2: k.update(uygun=False,neden='oturum-siniri')
    return k

@app.post('/start')
def start(job: Job):
    validate(job)
    if not re.fullmatch(r'FLG\{[a-f0-9]+\}',job.flag): raise HTTPException(400,'Geçersiz flag')
    with LOCK:
        cleanup(); rows=load()
        if job.oid in rows: return {'durum':'saglikli'}
        k=kapasite.simdi()
        if not k.uygun: return {'durum':'kuyrukta','neden':k.neden}
        if len(rows)>=2: return {'durum':'kuyrukta','neden':'oturum-siniri'}
        # Persist intent before starting Docker so a restart can clean a partially started session.
        try: subnet=allocate_subnet(rows)
        except RuntimeError: return {'durum':'hata','neden':'lab-agi-yok'}
        rows[job.oid]={'slug':job.slug,'expires':time.time()+2700,'subnet':subnet}; save(rows)
        env={**os.environ,'CYBERLAB_FLAG':job.flag,'CYBERLAB_SUBNET':subnet}
        code,_=run(runner.baslat_argv(job.slug,job.oid),timeout=180,env=env)
        if code:
            if stop_job(job.slug,job.oid): rows.pop(job.oid,None); save(rows)
            return {'durum':'hata','neden':'konteyner-baslatilamadi'}
        return {'durum':'saglikli'}

@app.post('/stop')
def stop(job: Job):
    validate(job)
    with LOCK:
        rows=load()
        if job.oid not in rows: return {'durum':'bitti'}
        if rows[job.oid]['slug']!=job.slug: raise HTTPException(404,'Oturum yok')
        ok=stop_job(job.slug,job.oid)
        if ok: rows.pop(job.oid,None); save(rows)
        return {'durum':'bitti' if ok else 'hata'}

def execute(job, parts):
    validate(job)
    with LOCK:
        row=load().get(job.oid)
        if not row or row['slug']!=job.slug or row['expires']<=time.time(): raise HTTPException(409,'Oturum sona erdi')
        argv=runner._argv(job.slug,job.oid,['exec','-T',SERVICE,'python','/opt/lab/exercise.py',*parts])
        return run(argv,timeout=20)

@app.post('/command')
def command(job: Job):
    try: parts=shlex.split(job.command)
    except ValueError: raise HTTPException(400,'Komut biçimi hatalı')
    if not parts or parts[0] not in COMMANDS or len(parts)>8 or any(len(p)>256 for p in parts):
        raise HTTPException(400,'Yalnız help, files, read, probe, patch, verify ve report komutları kullanılabilir')
    if parts[0]=='read' and (len(parts)!=2 or parts[1] not in {'source','logs','README'}):
        raise HTTPException(400,'Yalnız source, logs ve README okunabilir')
    code,out=execute(job,parts)
    return {'output':out,'exit_code':code}

@app.post('/verify')
def verify(job: Job):
    code,out=execute(job,['verify'])
    return {'basarili':code==0,'output':out}
