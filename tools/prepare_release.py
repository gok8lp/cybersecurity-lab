"""Idempotently generate shared lab manifests and the remaining foundational lessons."""
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'content/challenges.yaml'
data=yaml.safe_load(manifest.read_text(encoding='utf-8'))
guides={
 'scope-guard':'read source → probe 192.0.2.10 → flag gönder → patch allowlist → savunmayı doğrula. Gerçek ağ isteği yapılmaz.',
 'linux-permission-leak':'read source → probe → flag gönder → patch 600 → savunmayı doğrula. Yalnız bu labın geçici yedek dosyası değişir.',
 'path-shadow':'read source → probe → flag gönder → patch absolute-path → savunmayı doğrula. PATH kararı modellenir; host shell çalıştırılmaz.',
 'service-map':'probe → debug servisini bul → flag gönder → patch close-debug → savunmayı doğrula. Sağlanan servis haritası kullanılır; ağ taraması yoktur.',
 'http-info-leak':'read source → probe → sızan başlıktaki flag → patch no-debug → savunmayı doğrula.',
 'object-ownership':'read source → probe 1 ve probe 2 → flag gönder → patch owner-check → savunmayı doğrula.',
 'sqlite-parameter':'''read source → probe "' OR 1=1 --" → flag gönder → patch parameterized → savunmayı doğrula. Sorgu tek kullanımlık, bellek içi SQLite üzerinde çalışır.''',
 'auth-log-hunt':'read logs → probe <olay-kimliği> → kanıt flag değerini gönder → patch correlation → savunmayı doğrula.',
 'c-stack-boundary':'read source → probe → ASan bulgusunu incele → flag gönder → patch bounded → savunmayı doğrula. Sağlanan C kaynakları konteynerde gerçekten derlenir.',
 'c-format-string':'read source → probe → kontrollü format yorumlamasını gözle → flag gönder → patch fixed-format → savunmayı doğrula.',
 'cpp-raii-leak':'read source → probe → canlı kaynak sayacını incele → flag gönder → patch raii → savunmayı doğrula.',
 'container-least-privilege':'probe → kopya manifest risklerini incele → flag gönder → patch least-privilege → savunmayı doğrula. Host Docker ayarları değişmez.',
 'final-incident':'''read logs → read source → probe "' OR 1=1 --" → flag gönder → patch parameterized → report "İlk erişim, log kanıtı, kök neden, düzeltme ve regresyonu açıklayan en az 80 karakterlik olay raporun" → savunmayı doğrula.''',
}
for item in data['challenges']:
    slug=item['slug']; item['guide']=guides[slug]
    if slug=='service-map': item['objective']='Sağlanan lab servis haritasında debug sızıntısını bul; health işlevini koruyarak kapat.'
    if slug=='linux-permission-leak': item['objective']='Geçici yedekteki dünya-okuma iznini kanıtla; dosya modunu 600 yaparak yetki modelini düzelt.'
    folder=ROOT/'labs'/slug; folder.mkdir(exist_ok=True)
    compose={'services':{'target':{
        'build':'../shared','image':'flugel-cyberlab/exercises:1.0','user':'1000:1000',
        'read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
        'tmpfs':['/tmp:uid=1000,gid=1000,mode=1777,size=32m,exec'],
        'environment':{'CYBERLAB_FLAG':'${CYBERLAB_FLAG:-unused}','CYBERLAB_CHALLENGE':slug},
        'mem_limit':'256m','cpus':0.5,'pids_limit':64,'networks':['labnet'],
        'healthcheck':{'test':['CMD','python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/',timeout=1)"],'interval':'2s','timeout':'2s','retries':15},
        'labels':{'com.flugel.cyberlab.managed':'true','com.flugel.cyberlab.challenge':slug},
        'logging':{'driver':'json-file','options':{'max-size':'1m','max-file':'1'}}
    }},'networks':{'labnet':{'internal':True,'ipam':{'config':[{'subnet':'${CYBERLAB_SUBNET:-10.213.0.0/28}'}]},'labels':{'com.flugel.cyberlab.managed':'true'}}}}
    (folder/'compose.yaml').write_text(yaml.safe_dump(compose,sort_keys=False),encoding='utf-8')
manifest.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')

lessons=[
('06-ag-ve-kapsam','ag-ve-kapsam','network','Ağ sınırı: IP, port ve servis','kapsam-etik',
'''Bir IP makineyi, port o makinedeki dinleyiciyi belirtir. TCP bağlantısı SYN, SYN/ACK ve ACK ile kurulur. TLS bağlantıyı şifreler; uygulamanın yetkilendirme hatasını düzeltmez.

## Keşif
`service-map` labında yalnız sağlanan servis haritasını incele. Debug servisi gereksiz bilgi verirken health servisi normal işlevi temsil eder. Gerçek LAN adreslerine paket gönderilmez.

## Savunma
Gereksiz servisi kapat; health erişimini koru. Her şeyi kapatmak güvenli bir düzeltme değildir. `scope-guard` görevi de reddetme ve normal hedefi kabul etme koşullarını birlikte öğretir.

## Kontrol sorusu
443 portunun açık olması uygulamanın yetki kontrolünün doğru olduğunu kanıtlar mı? Hayır: port erişimi ile nesne yetkisi farklı katmanlardır.'''),
('07-kimlik-ve-yetki','kimlik-ve-yetki','identity','Kimlik doğrulama ve nesne sahipliği','http-temelleri',
'''Authentication kim olduğunu, authorization hangi nesneye hangi işlemi yapabileceğini belirler. Kullanıcının oturum açması bütün notlara erişebileceği anlamına gelmez.

## Keşif
`object-ownership` içinde `probe 1` normal öğrenci notunu, `probe 2` başka bir oyuncak kullanıcının kaydını temsil eder. İlk sürüm yalnız nesne kimliğini kontrol eder.

## Düzeltme
Sorguda hem nesne kimliğini hem sunucudan gelen kullanıcı kimliğini filtrele: `WHERE id=? AND owner_id=?`. Tarayıcıdan gelen owner_id güvenilir değildir.

## Regresyon
Başka kullanıcının notu reddedilmeli, kendi notun erişilebilir kalmalı. Kontrol sorusu: bağlantıyı arayüzden gizlemek yeterli mi? Hayır, sunucu kontrolü gerekir.'''),
('08-parametrik-sorgu','parametrik-sorgu','injection','SQL: veri ile komutu ayır','http-temelleri',
'''String birleştirmesi kullanıcı girdisini SQL söz dizimine dönüştürebilir. Parametrik sorgu değeri ayrı bağlar; kaçış karakterlerini elle yönetmek yerine sürücüyü kullanır.

```python
db.execute("SELECT name FROM users WHERE name=? AND password=?", (name, password))
```

## Keşif ve savunma
`sqlite-parameter` labı bellek içi bir eğitim veritabanı kullanır. `read source` ile sorguyu gör, kontrollü `probe` ile farkı gözle. `patch parameterized` sonra aynı girdi artık giriş sağlayamamalı; normal veri sorgusu çalışmalı.

Gerçek uygulamalarda ayrıca parola özeti, rate limit ve yetkilendirme gerekir. Kontrol sorusu: prepared statement nesne sahipliği kontrolünün yerine geçer mi? Hayır.'''),
('09-log-analizi','log-analizi','blue-team','Logdan kanıta: olay korelasyonu','http-temelleri',
'''Tek bir başarısız giriş alarm için yeterli değildir. Zaman penceresi, oturum/istek kimliği ve normal davranışla karşılaştırma gerekir. IP adresi tek başına kimlik kanıtı değildir.

## İnceleme
`auth-log-hunt` içinde `read logs` ile verilen sentetik kaydı oku. Kısa aralıkta tekrarlanan başarısızlıkları aynı correlation ID altında grupla. `probe <id>` ile hipotezini sınayabilirsin.

## Savunma
`correlation` kuralı saldırı desenini yakalamalı ve normal req-17 oturumunu alarm dışı bırakmalı. Hassas parola veya token loglanmamalıdır.

Kontrol sorusu: başarılı giriş önceki başarısızlıkları önemsiz yapar mı? Hayır; başarısız denemelerden sonraki başarı ele geçirilme işareti olabilir.'''),
('10-bellek-ve-raii','bellek-ve-raii','memory','C sınırları, format ve C++ RAII','linux-izinleri',
'''C dizisinde sonlandırıcı dahil kapasite hesaplanmalıdır. `strcpy` hedef kapasitesini bilmez. Format metni de veri değildir: `printf(input)` yerine `printf("%s", input)` kullan.

## Üç ayrı lab
`c-stack-boundary` örneği AddressSanitizer ile gerçek konteynerde derlenir. Uzun girdi sınır dışında yazma bulgusu üretir. `bounded` yaması uzunluğu kontrol eder.

`c-format-string` yalnız kontrollü MARKER argümanını kullanır; gerçek süreç belleği veya host adresi araştırılmaz. Sabit format girdiyi olduğu gibi basmalıdır.

`cpp-raii-leak` örneğinde exception erken dönüşü taklit eder. Ham pointer kaynağı açık bırakırken `unique_ptr` destructor ile bırakır. Doğrulama canlı kaynak sayacının sıfır olduğunu kontrol eder.

Kontrol sorusu: testin çökmemesi tek başına güvenlik kanıtı mı? Hayır; normal, sınır ve hatalı girişler ayrı test edilmelidir.'''),
('11-olay-mudahalesi','olay-mudahalesi','final','En az yetkiden olay raporuna','log-analizi',
'''Konteyner izolasyonu tek bir ayar değildir: salt okunur kök, düşürülmüş capability, no-new-privileges, kaynak sınırları ve internetsiz ağ birlikte gerekir. Host socket bağlamak bu sınırı aşar.

## Kopya manifest
`container-least-privilege` gerçek host ayarlarını değiştirmeden bir örnek üzerinde yanlış yetkileri inceletir. En az yetkili seçim normal health davranışını korumalıdır.

## Final
`final-incident` için önce Linux izinleri, parametrik sorgu, C sınırı ve log lablarını savunma doğrulamasıyla tamamla. Logu oku, kaynağı incele, sızıntıyı oyuncak hedefte kanıtla, düzelt ve regresyonu geçir.

Olay raporu beş şeyi içermeli: giriş vektörü, kanıt, kök neden, düzeltme, doğrulama. Labdaki uzunluk kontrolü yalnız asgari rapor varlığını doğrular; yazının teknik kalitesini insan değerlendirmelidir.

Kontrol sorusu: erişimi tamamen kesmek normal işlevi koruyan bir yama mıdır? Hayır; negatif ve pozitif regresyon birlikte geçmelidir.''')]
# Existing slugs are read from front matter rather than inferred from filenames.
existing={yaml.safe_load(p.read_text(encoding='utf-8').split('---',2)[1])['slug'] for p in (ROOT/'content/lessons').glob('*.md')}
aliases={'http-temelleri':None,'linux-izinleri':None,'kapsam-etik':None}
for value in list(aliases):
    if value not in existing:
        aliases[value]=next((s for s in existing if value.split('-')[0] in s), 'baslarken')
for file,slug,module,title,prereq,body in lessons:
    meta={'slug':slug,'module':module,'title':title,'type':'theory','minutes':10,'prerequisites':[aliases.get(prereq) or prereq]}
    (ROOT/'content/lessons'/f'{file}.md').write_text('---\n'+yaml.safe_dump(meta,allow_unicode=True,sort_keys=False)+'---\n# '+title+'\n\n'+body+'\n',encoding='utf-8')
