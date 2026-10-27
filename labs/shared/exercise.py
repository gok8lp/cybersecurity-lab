"""Disposable teaching targets. Bounded commands, synthetic data, no external targets."""
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

SLUG=os.getenv('CYBERLAB_CHALLENGE','linux-permission-leak')
STATE=Path(os.getenv('LAB_STATE','/tmp/cyberlab'))
STATE.mkdir(parents=True,exist_ok=True)
FLAG=os.getenv('CYBERLAB_FLAG','FLG{test}')
POLICY=STATE/'policy.json'
CHOICES={
 'scope-guard':('allowlist','yalnız target-lab hedefini kabul et'),
 'linux-permission-leak':('600','yedek dosyasını yalnız sahibi okuyabilsin'),
 'path-shadow':('absolute-path','mutlak program yolu kullan'),
 'service-map':('close-debug','debug servisini kapat, health servisini koru'),
 'http-info-leak':('no-debug','debug başlığını kaldır'),
 'object-ownership':('owner-check','her nesnede sahipliği denetle'),
 'sqlite-parameter':('parameterized','parametrik sorguya geç'),
 'auth-log-hunt':('correlation','olay kimliğine göre tespit et'),
 'c-stack-boundary':('bounded','girdi sınırı uygula'),
 'c-format-string':('fixed-format','sabit format kullan'),
 'cpp-raii-leak':('raii','kaynağı nesne ömrüne bağla'),
 'container-least-privilege':('least-privilege','salt okunur ve yetkisiz hedef seç'),
 'final-incident':('parameterized','log kanıtından parametrik sorgu savunmasına geç'),
}
CODES={
 'c-stack-boundary':('#include <string.h>\nint main(void){char b[8]; strcpy(b,"0123456789ABCDEF"); return b[0]==0;}','''#include <string.h>
int main(void){char b[8]; const char *s="0123456789ABCDEF"; if(strlen(s)>=sizeof b) return 0; memcpy(b,s,strlen(s)+1); return 0;}'''),
 'c-format-string':('#include <stdio.h>\nint main(void){const char *input="%s"; printf(input,"MARKER"); return 0;}','#include <stdio.h>\nint main(void){const char *input="%s"; printf("%s",input); return 0;}'),
 'cpp-raii-leak':('''#include <stdexcept>
int live=0; struct R {R(){++live;} ~R(){--live;}};
int main(){try {auto *p=new R; (void)p; throw 1;}catch(...){} return live==0?0:1;}''','''#include <memory>
int live=0; struct R {R(){++live;} ~R(){--live;}};
int main(){try {auto p=std::make_unique<R>(); throw 1;}catch(...){} return live==0?0:1;}''')}

def initialize():
    if not POLICY.exists():
        POLICY.write_text(json.dumps({'mode':'vulnerable','evidence':False,'report':''}))
        (STATE/'backup.txt').write_text(FLAG); (STATE/'backup.txt').chmod(0o644)
def policy(): initialize(); return json.loads(POLICY.read_text())
def put(p): POLICY.write_text(json.dumps(p))
def patched(p): return p['mode']==CHOICES[SLUG][0]

def sql_probe(payload,safe,password='wrong'):
    db=sqlite3.connect(':memory:'); db.execute('CREATE TABLE users(name TEXT, password TEXT)')
    db.execute('INSERT INTO users VALUES (?,?)',('student','correct-training-password'))
    try:
        if safe: row=db.execute('SELECT name FROM users WHERE name=? AND password=?',(payload,password)).fetchone()
        else: row=db.execute("SELECT name FROM users WHERE name='"+payload+"' AND password='"+password+"'").fetchone()
        return bool(row)
    except sqlite3.Error: return False
    finally: db.close()

def code_test(safe):
    vulnerable,fixed=CODES[SLUG]; src=STATE/('sample.cpp' if SLUG.startswith('cpp') else 'sample.c')
    src.write_text(fixed if safe else vulnerable)
    exe=STATE/'sample'
    cmd=['g++' if SLUG.startswith('cpp') else 'gcc',str(src),'-o',str(exe)]
    if SLUG=='c-stack-boundary': cmd+=['-fsanitize=address','-g']
    build=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
    if build.returncode: return False,build.stderr[-2000:]
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=3,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
    if SLUG=='c-format-string': return result.stdout=='%s',result.stdout
    return result.returncode==0,(result.stdout+result.stderr)[-2000:]

def probe(args,p):
    safe=patched(p); evidence=False; output=''
    target=args[0] if args else ''
    if SLUG=='linux-permission-leak':
        denied=(STATE/'backup.txt').stat().st_mode & 0o004 == 0
        evidence=not denied; output='ogrenci: erişim reddedildi' if denied else (STATE/'backup.txt').read_text()
    elif SLUG in {'sqlite-parameter','final-incident'}:
        evidence=sql_probe(target,safe); output='Erişim reddedildi' if not evidence else 'Oyuncak sorguda yetkisiz giriş doğrulandı.'
    elif SLUG=='object-ownership':
        evidence=target=='2' and not safe; output='403: sahiplik kontrolü' if safe and target=='2' else 'Not 1: normal öğrenci notu' if target=='1' else 'Not 2: başka oyuncak kullanıcıya ait kayıt' if evidence else 'probe 1 veya probe 2'
    elif SLUG=='http-info-leak':
        evidence=not safe; output='HTTP 200\nX-Debug-Flag: '+FLAG if evidence else 'HTTP 200\nContent-Type: text/plain\nhealth: ok'
    elif SLUG=='scope-guard':
        # Simulated routing decision only. No packets are sent.
        evidence=target!='target-lab' and not safe
        output='KARAR: '+('RED' if safe and target!='target-lab' else 'İZİN')+' (ağ isteği yapılmadı)'
    elif SLUG=='path-shadow':
        evidence=not safe; output='/tmp/student/bin/status (gölgelenmiş)' if evidence else '/usr/bin/status (güvenilen mutlak yol)'
    elif SLUG=='service-map':
        evidence=not safe; output='target-lab:8080 health OK'+('\ntarget-lab:9000 debug FLAG sızıntısı' if evidence else '\n9000: kapalı')
    elif SLUG=='auth-log-hunt':
        evidence=target=='req-42'; output='Tespit: req-42, 6 başarısız giriş / 60 saniye; normal req-17 hariç.' if evidence else 'Olay kimliğini bul: read logs; probe <correlation-id>'
    elif SLUG=='container-least-privilege':
        evidence=not safe; output='Kopya manifest: privileged=true, read_only=false, cap_drop=[]' if evidence else 'Kopya manifest: privileged=false, read_only=true, cap_drop=[ALL]'
    elif SLUG in CODES:
        ok,detail=code_test(safe); evidence=not ok
        output=detail or ('Regresyon başarılı' if ok else 'Kaynak sayacı sıfıra dönmedi')
        if SLUG=='c-format-string': evidence=not safe
    if evidence:
        p['evidence']=True; put(p)
        if SLUG=='final-incident' and target=="' OR 1=1 --": output+='\nİlk erişim vektörü: SQL string birleştirmesi.'
        output+='\nKanıt: '+FLAG
    return output

def verify(p):
    checks={'kanit_toplandi':p['evidence'],'dogru_savunma':patched(p)}
    if SLUG=='linux-permission-leak': checks['yetkisiz_okuma_engelli']=(STATE/'backup.txt').stat().st_mode & 0o077 == 0
    if SLUG in {'sqlite-parameter','final-incident'}:
        checks['enjeksiyon_engelli']=not sql_probe("' OR 1=1 --",patched(p))
        checks['normal_islev']=sql_probe('student',patched(p),'correct-training-password')
        checks['yanlis_parola_engelli']=not sql_probe('student',patched(p),'wrong')
    elif SLUG in CODES: checks['derleme_ve_regresyon']=code_test(patched(p))[0]
    else: checks['normal_islev']=patched(p)
    if SLUG=='final-incident': checks['olay_raporu']=len(p['report'].strip())>=80
    print(json.dumps(checks,ensure_ascii=False,indent=2)); return 0 if all(checks.values()) else 1

def main(args):
    p=policy(); cmd=args[0] if args else 'help'; rest=args[1:]
    if cmd=='help':
        print('files | read source | read logs | probe [girdi] | patch <seçim> | verify | report <metin>\n'
              'Bu sınırlandırılmış lab konsoludur; shell veya gerçek ağ erişimi sağlamaz.\n'
              'Savunma seçenekleri: '+', '.join([CHOICES[SLUG][0],'disabled','unchanged'])+'\nAmaç: '+CHOICES[SLUG][1]); return 0
    if cmd=='files': print('source\nlogs\nREADME'); return 0
    if cmd=='read':
        name=rest[0] if rest else ''
        if name=='source':
            print(CODES[SLUG][1 if patched(p) else 0] if SLUG in CODES else {
                'sqlite-parameter':"SELECT name FROM users WHERE name='"+'<input>'+"' AND password='wrong'",
                'final-incident':"query = \"SELECT name FROM users WHERE name='\" + input + \"' AND password='wrong'\"",
                'linux-permission-leak':'backup.txt sahibi: app; izin 0644. ogrenci dünya-okuma bitiyle erişiyor.',
                'object-ownership':'GET /notes/{id} -> notes[id] # owner kontrolü eksik',
                'http-info-leak':'response.headers["X-Debug-Flag"] = session_flag',
            }.get(SLUG,CHOICES[SLUG][1]))
        elif name=='logs': print('12:00:01 req-17 login OK\n'+'\n'.join(f'12:00:{10+i:02d} req-42 login FAIL' for i in range(6))+'\n12:01:01 req-42 unexpected login OK')
        elif name=='README': print('Önce kaynağı ve logu incele, probe ile kanıt topla, flag gönder, patch uygula ve savunmayı doğrula.')
        else: print('Yalnız source, logs, README okunabilir'); return 1
        return 0
    if cmd=='probe': print(probe(rest,p)); return 0
    if cmd=='patch':
        mode=rest[0] if rest else ''
        if mode not in {CHOICES[SLUG][0],'disabled','unchanged'}: print('Geçersiz seçenek; help'); return 1
        p['mode']=mode; put(p)
        if SLUG=='linux-permission-leak': (STATE/'backup.txt').chmod(0o600 if mode=='600' else 0o644)
        print('Savunma uygulandı. verify ile hem erişim engelini hem normal işlevi sınayın.'); return 0
    if cmd=='verify': return verify(p)
    if cmd=='report':
        p['report']=' '.join(rest)[:4096]; put(p); print('Olay raporu kaydedildi.'); return 0
    print('Bilinmeyen komut: help'); return 1

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'lab healthy')
    def log_message(self,*args): pass

if __name__=='__main__':
    if sys.argv[1:] == ['serve']:
        signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
        initialize(); HTTPServer(('127.0.0.1',8080),Health).serve_forever()
    else: sys.exit(main(sys.argv[1:]))
