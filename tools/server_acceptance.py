"""Run on the deployment host. A temporary API database isolates acceptance XP from real progress."""
import os
import re
import tempfile
import time
from pathlib import Path
from fastapi.testclient import TestClient
from cyberlab.service import uygulama
from cyberlab.broker import Broker
from runner import runner
from labs.shared.advanced import MODES
from cyberlab.content import challenge_yukle

PROBES={'scope-guard':'probe 192.0.2.10','object-ownership':'probe 2','sqlite-parameter':'''probe "' OR 1=1 --"''',
        'auth-log-hunt':'probe req-42','final-incident':'''probe "' OR 1=1 --"'''}
PATCH={'scope-guard':'allowlist','linux-permission-leak':'600','path-shadow':'absolute-path','service-map':'close-debug',
       'http-info-leak':'no-debug','object-ownership':'owner-check','sqlite-parameter':'parameterized','auth-log-hunt':'correlation',
       'c-stack-boundary':'bounded','c-format-string':'fixed-format','cpp-raii-leak':'raii','container-least-privilege':'least-privilege','final-incident':'parameterized'}

PATCH.update(MODES)

def main():
    with tempfile.TemporaryDirectory() as data:
        os.environ['CYBERLAB_DATA']=data
        broker=Broker(os.environ.get('CYBERLAB_RUNNER_SOCKET','/run/cyberlab/runner.sock'))
        with TestClient(uygulama(runner=broker)) as c:
            def start_ready(slug):
                deadline=time.monotonic()+180
                while True:
                    response=c.post('/api/sessions',json={'challenge':slug})
                    assert response.status_code==200,response.text
                    lab=response.json()
                    if lab['state']=='saglikli': return lab
                    if lab['state']!='kuyrukta' or time.monotonic()>=deadline:
                        raise AssertionError(lab)
                    # Honor production capacity protection while other host workloads fluctuate.
                    print('WAIT capacity:',lab.get('neden'),flush=True)
                    time.sleep(10)
            slugs=list(challenge_yukle())
            for slug in slugs:
                lab=start_ready(slug)
                oid=lab['id']
                try:
                    def command(value):
                        r=c.post(f'/api/sessions/{oid}/command',json={'command':value})
                        assert r.status_code==200,r.text
                        return r.json()
                    output=command(PROBES.get(slug,'probe'))['output']
                    found=re.search(r'FLG\{[a-f0-9]+\}',output); assert found,slug+': no evidence'
                    assert c.post(f'/api/sessions/{oid}/submit',json={'flag':found.group()}).json()['sonuc']=='dogru'
                    command('patch disabled')
                    assert c.post(f'/api/sessions/{oid}/verify',json={}).json()['basarili'] is False
                    command('patch '+PATCH[slug])
                    if slug=='final-incident':
                        command('report "SQL birleştirmesi req-42 oturumunda ilk erişimi sağladı. Log ve sorgu kanıtlandı; parametrik sorgu uygulandı, enjeksiyon reddedildi ve normal sorgu çalıştı."')
                    result=c.post(f'/api/sessions/{oid}/verify',json={})
                    assert result.status_code==200 and result.json()['basarili'],slug+': '+result.text
                    assert result.json()['xp']>0
                    print('PASS attack + wrong defense + corrected defense + cleanup:',slug,flush=True)
                finally:
                    c.post(f'/api/sessions/{oid}/stop',json={})
            # 20 start/extend/reset/stop cycles with fresh identities and independent networks.
            for n in range(20):
                lab=start_ready('scope-guard'); oid=lab['id']
                try:
                    output=c.post(f'/api/sessions/{oid}/command',json={'command':'probe 192.0.2.10'}).json()['output']
                    flag=re.search(r'FLG\{[a-f0-9]+\}',output).group()
                    extended=c.post(f'/api/sessions/{oid}/extend',json={})
                    assert extended.status_code==200 and extended.json()['extended'],extended.text
                    assert c.post(f'/api/sessions/{oid}/extend',json={}).status_code==409
                    reset=c.post(f'/api/sessions/{oid}/reset',json={})
                    assert reset.status_code==200,reset.text
                    lab=reset.json()
                    if lab['state']=='kuyrukta': lab=start_ready('scope-guard')
                    assert lab['state']=='saglikli' and lab['id']!=oid,lab
                    assert c.post(f'/api/sessions/{oid}/command',json={'command':'help'}).status_code==409
                    oid=lab['id']
                    assert c.post(f'/api/sessions/{oid}/submit',json={'flag':flag}).json()['sonuc']!='dogru'
                finally:
                    assert c.post(f'/api/sessions/{oid}/stop',json={}).status_code==200
                if (n+1)%5==0: print(f'PASS lifecycle cycles: {n+1}/20',flush=True)
            print('PASS 20 consecutive lifecycle cycles',flush=True)
        import subprocess
        for kind in ('container','network','volume'):
            result=subprocess.run(['docker',kind,'ls','--filter','label=com.flugel.cyberlab.managed=true','--quiet'],capture_output=True,text=True,check=True)
            assert not result.stdout.strip(),f'Orphan {kind}: {result.stdout}'
        print('PASS zero managed orphan containers/networks/volumes',flush=True)

if __name__=='__main__': main()
