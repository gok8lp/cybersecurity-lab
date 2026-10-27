from datetime import timedelta
import importlib.util
from pathlib import Path
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from cyberlab.service import uygulama
from cyberlab.models import LabSession, simdi
from cyberlab.content import ders_yukle, challenge_yukle
from runner import service

ROOT=Path(__file__).resolve().parents[1]
class Runner:
    def __init__(self): self.flags={}; self.fixed=False; self.stopped=[]; self.expiry={}
    def kapasite(self): return {'uygun':True,'neden':None}
    def baslat(self,slug,oid,flag): self.flags[oid]=flag; self.expiry[oid]=simdi().timestamp()+2700; return {'durum':'saglikli'}
    def uzat(self,slug,oid): self.expiry[oid]+=900; return {'expires':self.expiry[oid]}
    def durdur(self,slug,oid): self.stopped.append(oid); return {'durum':'bitti'}
    def komut(self,slug,oid,command): return {'output':'bounded console','exit_code':0}
    def dogrula(self,slug,oid): return {'basarili':self.fixed,'output':'regression'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('CYBERLAB_DATA',str(tmp_path))
    r=Runner(); app=uygulama(f'sqlite:///{tmp_path / "db.sqlite"}',runner=r)
    with TestClient(app) as c: yield c,r,app

def start(c,slug='linux-permission-leak'):
    response=c.post('/api/sessions',json={'challenge':slug}); assert response.status_code==200,response.text
    return response.json()['id']

def test_full_attack_defense_awards_once(client):
    c,r,_=client; oid=start(c)
    assert c.post(f'/api/sessions/{oid}/verify',json={}).status_code==409
    assert c.post(f'/api/sessions/{oid}/submit',json={'flag':r.flags[oid]}).json()['sonuc']=='dogru'
    assert c.post(f'/api/sessions/{oid}/verify',json={}).json()['basarili'] is False
    assert c.get('/api/progress').json()['xp']==0
    r.fixed=True
    result=c.post(f'/api/sessions/{oid}/verify',json={}).json()
    assert result['basarili'] and result['xp']==220
    assert oid in r.stopped
    assert c.post(f'/api/sessions/{oid}/verify',json={}).status_code==409
    assert c.post(f'/api/sessions/{oid}/command',json={'command':'help'}).status_code==409
    oid2=start(c); c.post(f'/api/sessions/{oid2}/submit',json={'flag':r.flags[oid2]})
    assert c.post(f'/api/sessions/{oid2}/verify',json={}).json()['xp']==0

def test_expired_flag_and_command_rejected(client):
    c,r,app=client; oid=start(c)
    with Session(app.state.engine) as s:
        row=s.get(LabSession,oid); row.expires_at=simdi()-timedelta(seconds=1); s.add(row); s.commit()
    assert c.post(f'/api/sessions/{oid}/submit',json={'flag':r.flags[oid]}).status_code==409
    assert c.post(f'/api/sessions/{oid}/command',json={'command':'help'}).status_code==409
    assert c.get(f'/api/sessions/{oid}').json()['state']=='suresi-doldu'

def test_hint_cost_survives_reload_and_is_not_exposed(client):
    c,_,_=client
    puzzle=next(p for p in c.get('/api/puzzles').json() if p['slug']=='b64-coz')
    assert puzzle['ipuclari']==[] and puzzle['ipucu_sayisi']==3
    for n in range(3): assert len(c.post('/api/puzzles/b64-coz/hint',json={}).json()['ipuclari'])==n+1
    response=c.post('/api/puzzles/b64-coz/answer',json={'cevap':'Cyber Range'}).json()
    assert response['dogru'] and response['xp']==22
    assert c.post('/api/puzzles/b64-coz/answer',json={'cevap':'Cyber Range'}).json()['xp']==0

def test_lessons_dependencies_progress_streak(client):
    c,_,_=client
    assert c.post('/api/lessons/kapsam-etik/complete',json={}).status_code==409
    assert c.post('/api/lessons/baslarken/complete',json={}).json()['xp']==50
    assert c.post('/api/lessons/baslarken/complete',json={}).json()['xp']==0
    assert c.get('/api/progress').json()['streak']==1
    assert c.post('/api/lessons/kapsam-etik/complete',json={}).status_code==200

def test_limits_and_boundary(client):
    c,_,_=client; start(c); start(c)
    assert c.post('/api/sessions',json={'challenge':'linux-permission-leak'}).status_code==409
    assert c.post('/api/lessons/baslarken/complete',json={},headers={'Origin':'https://evil.test'}).status_code==403
    assert c.get('/api/health',headers={'Host':'evil.test'}).status_code==400
    assert c.post('/api/sessions',json={'challenge':'final-incident'}).status_code==409
    assert c.post('/api/puzzles/b64-coz/answer',json={'cevap':'x'*3000}).status_code==422

def test_content_complete():
    assert len(ders_yukle())>=20
    assert len(challenge_yukle())==21
    assert all(c.raw['guide'] for c in challenge_yukle().values())

@pytest.mark.parametrize('command',['sh','docker ps','; id','read /etc/passwd','curl https://example.org'])
def test_runner_rejects_arbitrary_execution(command,monkeypatch,tmp_path):
    monkeypatch.setattr(service,'ROOT',tmp_path)
    with TestClient(service.app) as c:
        response=c.post('/command',json={'slug':'linux-permission-leak','oid':'a'*12,'command':command})
        assert response.status_code in (400,409)

def test_reaper_only_stops_expired_registry_entries(monkeypatch,tmp_path):
    monkeypatch.setattr(service,'ROOT',tmp_path)
    service.save({'a'*12:{'slug':'linux-permission-leak','expires':0},'b'*12:{'slug':'http-info-leak','expires':9999999999}})
    stopped=[]
    monkeypatch.setattr(service,'stop_job',lambda slug,oid:stopped.append(oid) or True)
    service.cleanup()
    assert stopped==['a'*12] and list(service.load())==['b'*12]

def test_subnet_avoids_docker_routes_and_reserved_sessions(monkeypatch):
    replies=iter([(0,'network-id'),(0,'10.213.0.0/28\n'),
                  (0,'[{"dst":"default"},{"dst":"10.213.0.16/28"}]')])
    monkeypatch.setattr(service,'run',lambda argv:next(replies))
    assert service.allocate_subnet({'reserved':{'subnet':'10.213.0.32/28'}})=='10.213.0.48/28'

def test_subnet_inventory_failure_stops_allocation(monkeypatch):
    monkeypatch.setattr(service,'run',lambda argv:(1,'unavailable'))
    with pytest.raises(RuntimeError,match='inventory unavailable'):
        service.allocate_subnet({})

@pytest.mark.parametrize('slug,probe,mode',[
    ('linux-permission-leak',[],'600'),('sqlite-parameter',["' OR 1=1 --"],'parameterized'),
    ('object-ownership',['2'],'owner-check'),('http-info-leak',[],'no-debug'),
    ('auth-log-hunt',['req-42'],'correlation'),('scope-guard',['192.0.2.10'],'allowlist'),
    ('path-shadow',[],'absolute-path'),('service-map',[],'close-debug'),
    ('container-least-privilege',[],'least-privilege')])
def test_exercise_attack_wrong_patch_and_defense(tmp_path,slug,probe,mode):
    import os
    if os.name == 'nt' and slug == 'linux-permission-leak':
        pytest.skip('POSIX file modes are verified on the Linux deployment host')
    env={**os.environ,'LAB_STATE':str(tmp_path),'CYBERLAB_CHALLENGE':slug,'CYBERLAB_FLAG':'FLG{abc}'}
    def cmd(*args):
        return subprocess.run([sys.executable,'-X','utf8',str(ROOT/'labs/shared/exercise.py'),*args],env=env,text=True,encoding='utf-8',capture_output=True)
    assert cmd('verify').returncode==1
    assert 'FLG{abc}' in cmd('probe',*probe).stdout
    cmd('patch','disabled'); assert cmd('verify').returncode==1
    cmd('patch',mode); assert cmd('verify').returncode==0
    assert cmd('read','/etc/passwd').returncode==1


def test_session_reset_rotates_identity_and_flag(client):
    c,r,_=client; oid=start(c); old_flag=r.flags[oid]
    c.post(f'/api/sessions/{oid}/submit',json={'flag':old_flag})
    response=c.post(f'/api/sessions/{oid}/reset',json={})
    assert response.status_code==200,response.text
    new=response.json(); assert new['id']!=oid and new['previous_id']==oid
    assert oid in r.stopped and new['state']=='saglikli'
    assert c.post(f'/api/sessions/{new["id"]}/submit',json={'flag':old_flag}).json()['sonuc']!='dogru'
    assert c.post(f'/api/sessions/{oid}/command',json={'command':'help'}).status_code==409
    assert c.get('/api/progress').json()['xp']==0


def test_extend_once_and_reject_expired_session(client):
    c,r,app=client; oid=start(c); original=r.expiry[oid]
    result=c.post(f'/api/sessions/{oid}/extend',json={})
    assert result.status_code==200 and result.json()['extended'] is True
    assert r.expiry[oid]==original+900
    assert c.post(f'/api/sessions/{oid}/extend',json={}).status_code==409
    with Session(app.state.engine) as s:
        lab=s.get(LabSession,oid);lab.expires_at=simdi()-timedelta(seconds=1);s.add(lab);s.commit()
    assert c.post(f'/api/sessions/{oid}/extend',json={}).status_code==409


def test_broker_extension_is_retry_safe(monkeypatch,tmp_path):
    monkeypatch.setattr(service,'ROOT',tmp_path)
    future=simdi().timestamp()+2700
    service.save({'a'*12:{'slug':'linux-permission-leak','expires':future}})
    with TestClient(service.app) as c:
        payload={'slug':'linux-permission-leak','oid':'a'*12}
        first=c.post('/extend',json=payload).json()
        second=c.post('/extend',json=payload).json()
        assert first['expires']==second['expires']==future+900


@pytest.mark.parametrize('slug',[
    'web-output-encoding','path-traversal','csrf-token','jwt-signature',
    'password-storage','archive-slip','c-integer-boundary','binary-secret'])
def test_new_exercise_evidence_wrong_patch_and_regressions(tmp_path,slug):
    import os,shutil
    if slug in {'c-integer-boundary','binary-secret'} and not (shutil.which('gcc') and shutil.which('strings')):
        pytest.skip('C compilation and binary inspection run on Linux CI/deployment host')
    from labs.shared.advanced import MODES
    env={**os.environ,'LAB_STATE':str(tmp_path),'CYBERLAB_CHALLENGE':slug,'CYBERLAB_FLAG':'FLG{abc}'}
    def cmd(*args):
        return subprocess.run([sys.executable,'-X','utf8',str(ROOT/'labs/shared/exercise.py'),*args],env=env,text=True,encoding='utf-8',capture_output=True)
    assert cmd('verify').returncode==1
    result=cmd('probe');assert result.returncode==0 and 'FLG{abc}' in result.stdout,result.stdout+result.stderr
    cmd('patch','disabled');assert cmd('verify').returncode==1
    cmd('patch',MODES[slug]);result=cmd('verify')
    assert result.returncode==0,result.stdout+result.stderr
    import json
    assert all(json.loads(result.stdout).values())
    assert 'FLG{abc}' not in cmd('probe').stdout


def test_curriculum_links_and_new_modules(client):
    c,_,_=client
    lessons=c.get('/api/lessons').json(); challenges=c.get('/api/challenges').json()
    ids={item['slug'] for item in challenges}
    new=[item for item in lessons if item['introduced']=='1.1']
    assert len(new)==8 and all(item['challenge'] in ids for item in new)
    assert len([item for item in challenges if item['introduced']=='1.1'])==8
    assert all(len(c.get('/api/lessons/'+item['slug']).json()['body'])>1000 for item in new)
