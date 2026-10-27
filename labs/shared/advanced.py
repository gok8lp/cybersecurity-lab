"""Additional disposable exercises: real parsers, crypto, files and compiler checks."""
import base64
import hashlib
import hmac
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

MODES={
 'web-output-encoding':'escape-html', 'path-traversal':'confine-root',
 'csrf-token':'validate-token', 'jwt-signature':'pin-algorithm',
 'password-storage':'salted-scrypt', 'archive-slip':'validate-members',
 'c-integer-boundary':'check-before-cast', 'binary-secret':'external-secret',
}

INTEGER_VULNERABLE='''#include <stdint.h>
#include <stdlib.h>
int allowed(unsigned n){uint8_t size=(uint8_t)n; return size<8;}
int main(int argc,char **argv){unsigned n=argc>1?(unsigned)strtoul(argv[1],0,10):256; return n==4 ? (allowed(n)?0:1) : (allowed(n)?1:0);}
'''
INTEGER_FIXED=INTEGER_VULNERABLE.replace('uint8_t size=(uint8_t)n;', 'if(n>UINT8_MAX) return 0; uint8_t size=(uint8_t)n;')
BINARY_VULNERABLE='#include <stdio.h>\nint main(void){puts("TRAINING-KEY-47"); return 0;}\n'
BINARY_FIXED='#include <stdlib.h>\nint main(void){const char *secret=getenv("LAB_TRAINING_SECRET"); return secret && secret[0] ? 0:1;}\n'

def source(slug,safe):
    if slug=='c-integer-boundary': return INTEGER_FIXED if safe else INTEGER_VULNERABLE
    if slug=='binary-secret': return BINARY_FIXED if safe else BINARY_VULNERABLE
    return {
      'web-output-encoding':'rendered = "<p>" + '+('html.escape(input, quote=True)' if safe else 'input')+' + "</p>"',
      'path-traversal':'candidate = (public / input).resolve()\n'+('reject unless candidate.is_relative_to(public.resolve())' if safe else '# public sınırı denetlenmiyor'),
      'csrf-token':'POST /training/change\n'+('require same session + hmac.compare_digest(expected_token, request_token)' if safe else '# cookie var; CSRF token denetlenmiyor'),
      'jwt-signature': 'require HS256 and constant-time HMAC signature comparison' if safe else 'if header.alg == "none": accept payload without signature',
      'password-storage':'salt=os.urandom(16); hashlib.scrypt(password, salt=salt, n=16384, r=8, p=1)' if safe else 'digest=hashlib.sha256(password).hexdigest()  # salt yok, hızlı özet',
      'archive-slip':'for name in archive.namelist(): resolve destination; require destination under extraction root before write' if safe else 'for name in archive.namelist(): (destination / name).write_bytes(archive.read(name))',
    }[slug]

class Tags(HTMLParser):
    def __init__(self): super().__init__(); self.active=[]; self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script' or any(key.startswith('on') for key,_ in attrs): self.active.append(tag)
    def handle_data(self,data): self.text.append(data)

def render(value,safe):
    parser=Tags(); parser.feed('<p>'+(html.escape(value,quote=True) if safe else value)+'</p>'); return parser

def read_fixture(state,value,safe):
    root=(state/'paths').resolve(); public=root/'public'; private=root/'private'
    public.mkdir(parents=True,exist_ok=True); private.mkdir(exist_ok=True)
    (public/'hello.txt').write_text('normal training document')
    (private/'note.txt').write_text('private training note')
    candidate=(public/value).resolve()
    # Even the vulnerable variant stays within the disposable fixture, never the host filesystem.
    if not candidate.is_relative_to(root) or (safe and not candidate.is_relative_to(public)): return None
    return candidate.read_text() if candidate.is_file() else None

def b64(value): return base64.urlsafe_b64encode(value).rstrip(b'=').decode()

def jwt_token(secret,admin=False,unsigned=False):
    head=b64(json.dumps({'alg':'none' if unsigned else 'HS256'}).encode())
    body=b64(json.dumps({'sub':'admin' if admin else 'student'}).encode())
    signing=head+'.'+body
    return signing+'.'+('' if unsigned else b64(hmac.digest(secret,signing.encode(),'sha256')))

def jwt_user(token,secret,safe):
    try:
        head,body,signature=token.split('.')
        decode=lambda part:json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
        alg=decode(head)['alg']
        expected=b64(hmac.digest(secret,(head+'.'+body).encode(),'sha256'))
        valid=alg=='HS256' and hmac.compare_digest(signature,expected)
        if not valid and (safe or alg!='none'): return None
        return decode(body).get('sub')
    except (ValueError,KeyError,TypeError): return None

def csrf_accept(token,safe):
    expected='session-bound-training-token'
    return not safe or (bool(token) and hmac.compare_digest(expected,token))

def password_record(password,salt=None):
    salt=salt or os.urandom(16)
    return salt,hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)

def unpack_fixture(state,safe,malicious):
    root=(state/('zip-attack' if malicious else 'zip-normal')).resolve()
    destination=root/'unpacked'; destination.mkdir(parents=True,exist_ok=True)
    escaped=root/'outside.txt'
    escaped.unlink(missing_ok=True)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as archive:
        archive.writestr('../outside.txt' if malicious else 'notes.txt','training archive content')
    with zipfile.ZipFile(stream) as archive:
        for name in archive.namelist():
            path=(destination/name).resolve()
            if not path.is_relative_to(root): return False
            if safe and not path.is_relative_to(destination): return False
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(archive.read(name))
    return escaped.exists() if malicious else (destination/'notes.txt').read_text()=='training archive content'

def compile_sample(state,slug,safe):
    src=state/(slug+'.c'); exe=state/(slug+'.bin')
    src.write_text(source(slug,safe))
    built=subprocess.run(['gcc','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],capture_output=True,text=True,timeout=10)
    if built.returncode: raise RuntimeError(built.stderr[-2000:])
    return exe

def probe(slug,safe,args,state):
    if slug=='web-output-encoding':
        payload=args[0] if args else '<script>training()</script>'
        parser=render(payload,safe)
        return bool(parser.active),'HTML parser etkin etiketleri: '+repr(parser.active)+'; metin: '+repr(''.join(parser.text))
    if slug=='path-traversal':
        value=args[0] if args else '../private/note.txt'
        result=read_fixture(state,value,safe)
        return result=='private training note','Dosya sonucu: '+(result or 'erişim reddedildi')
    if slug=='csrf-token':
        value=args[0] if args else ''
        accepted=csrf_accept(value,safe)
        return accepted and value!='session-bound-training-token','Eğitim isteği '+('kabul edildi' if accepted else 'reddedildi')+' (gerçek hesap/HTTP isteği yok)'
    if slug=='jwt-signature':
        secret=b'training-signing-secret'; token=jwt_token(secret,True,True)
        user=jwt_user(token,secret,safe)
        return user=='admin','İmzasız eğitim tokenı: '+token+'\nDoğrulanan rol: '+str(user)
    if slug=='password-storage':
        password='training-sunflower'; candidates=['training-river',password,'training-cloud']
        if safe:
            salt,digest=password_record(password)
            return False,'scrypt: salt='+salt.hex()+'; hızlı SHA-256 sözlük eşleştirmesi uygulanamaz. Zayıf parolalar yine risklidir.'
        digest=hashlib.sha256(password.encode()).digest()
        found=next((word for word in candidates if hashlib.sha256(word.encode()).digest()==digest),None)
        return found is not None,'Üç kelimelik eğitim sözlüğünden eşleşme: '+str(found)
    if slug=='archive-slip':
        escaped=unpack_fixture(state,safe,True)
        return escaped,'ZIP üyesi ../outside.txt: '+('hedef dizinin dışına yazıldı' if escaped else 'reddedildi')
    exe=compile_sample(state,slug,safe)
    if slug=='c-integer-boundary':
        result=subprocess.run([str(exe),'256'],capture_output=True,text=True,timeout=3)
        return result.returncode==1,'256 değeri uint8_t içine daraltılınca 0 olur. Sınır testi dönüş kodu: '+str(result.returncode)
    dumped=subprocess.run(['strings',str(exe)],capture_output=True,text=True,timeout=3)
    exposed='TRAINING-KEY-47' in dumped.stdout
    return exposed,'strings eşleşmesi: '+('TRAINING-KEY-47' if exposed else 'gömülü eğitim anahtarı yok')

def verify(slug,safe,state):
    evidence,_=probe(slug,safe,[],state)
    checks={'saldiri_engelli':not evidence}
    if slug=='web-output-encoding':
        parser=render('Merhaba <öğrenci> & "not"',safe)
        checks['normal_metin_korundu']=''.join(parser.text)=='Merhaba <öğrenci> & "not"'
    elif slug=='path-traversal': checks['normal_dosya']=read_fixture(state,'hello.txt',safe)=='normal training document'
    elif slug=='csrf-token':
        checks['dogru_token']=csrf_accept('session-bound-training-token',safe)
        checks['yanlis_token_engelli']=not csrf_accept('wrong',safe)
    elif slug=='jwt-signature':
        secret=b'training-signing-secret'
        good=jwt_token(secret); head,_,sig=good.split('.')
        tampered=head+'.'+b64(b'{"sub":"admin"}')+'.'+sig
        checks.update(normal_token=jwt_user(good,secret,safe)=='student',degistirilmis_token_engelli=jwt_user(tampered,secret,safe) is None)
    elif slug=='password-storage':
        a,da=password_record('training-sunflower'); b,db=password_record('training-sunflower')
        checks.update(farkli_salt=a!=b and da!=db,dogru_parola=hmac.compare_digest(da,password_record('training-sunflower',a)[1]),yanlis_parola_engelli=not hmac.compare_digest(da,password_record('wrong',a)[1]))
    elif slug=='archive-slip': checks['normal_zip']=unpack_fixture(state,safe,False)
    else:
        exe=compile_sample(state,slug,safe)
        env={**os.environ,'LAB_TRAINING_SECRET':'provided-at-runtime'}
        normal=subprocess.run([str(exe),'4'],env=env,capture_output=True,timeout=3)
        checks['normal_islev']=normal.returncode==0
        if slug=='binary-secret':
            env.pop('LAB_TRAINING_SECRET')
            checks['eksik_secret_reddedildi']=subprocess.run([str(exe)],env=env,capture_output=True,timeout=3).returncode!=0
    return checks
