import { useEffect, useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Progress = { xp:number; tamamlanan:string[]; streak:number; level:number; review:{slug:string; days:number}[] };
type Lesson = { slug:string; module:string; title:string; minutes:number; prerequisites:string[]; challenge?:string; introduced:string };
type Puzzle = {slug:string; baslik:string; kategori:string; soru:string; xp:number; cevap_tipi:string; secenekler:string[]; ipuclari:string[]; ipucu_sayisi:number};
type Challenge = {slug:string; title:string; module:string; objective:string; guide:string; score:number; prerequisites:string[]; difficulty:string; introduced:string};
type Lab = {id:string; challenge:string; state:string; expires_at:string; extended:boolean; neden?:string};
type Event = {id:number; action:string; subject:string; result:string; created_at:string};

async function request<T>(path:string, body?:unknown):Promise<T> {
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),195000);
  try {
    const r=await fetch('/api'+path,{signal:controller.signal,...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
    const data=await r.json();
    if(!r.ok) throw new Error(typeof data.detail==='string'?data.detail:`İstek başarısız (${r.status})`);
    return data;
  } finally {clearTimeout(timer);}
}
const reasons:Record<string,string>={'runner-yok':'Lab servisine erişilemiyor','bellek-az':'Sunucuda boş bellek eşiği sağlanmıyor','disk-mesgul':'Sunucu diski meşgul','yuk-yuksek':'Sunucu yükü yüksek','oturum-siniri':'Önce etkin lablardan birini durdur','konteyner-baslatilamadi':'Lab konteyneri başlatılamadı'};
const states:Record<string,string>={saglikli:'Keşfe hazır','saldiri-tamam':'Savunma aşaması',bitti:'Kapalı','suresi-doldu':'Süre doldu',hata:'Başlatılamadı',kuyrukta:'Şu an başlatılamıyor','runner-yok':'Lab servisi yok'};
const modules:Record<string,string>={safety:'Güvenli başlangıç',linux:'Linux',network:'Ağ',web:'Web güvenliği',identity:'Kimlik ve oturum',injection:'Enjeksiyon', 'blue-team':'Log ve savunma',memory:'C / C++ belleği',reverse:'Binary inceleme',container:'Konteyner',final:'Final'};
const categories:Record<string,string>={kodlama:'Kodlama',ozet:'Özet',izinler:'Linux',http:'Web','guvenli-kod':'Güvenli kod',dayaniklilik:'Dayanıklılık',log:'Log'};

function MarkdownText({text}:{text:string}) {return <div className="metin"><Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown></div>;}

export function Uygulama(){
  const [tab,setTab]=useState(location.hash.slice(1)||'ana');
  const [progress,setProgress]=useState<Progress>({xp:0,tamamlanan:[],streak:0,level:1,review:[]});
  const [lessons,setLessons]=useState<Lesson[]>([]),[puzzles,setPuzzles]=useState<Puzzle[]>([]),[challenges,setChallenges]=useState<Challenge[]>([]);
  const [labs,setLabs]=useState<Lab[]>([]),[capacity,setCapacity]=useState<{uygun:boolean;neden?:string}|null>(null),[events,setEvents]=useState<Event[]>([]);
  const [error,setError]=useState(''),[loading,setLoading]=useState(true),[busy,setBusy]=useState('');
  const [labFilter,setLabFilter]=useState('hepsi'),[labSearch,setLabSearch]=useState(''),[targetLab,setTargetLab]=useState('');
  async function refresh(){
    const [p,l,ps,c,s,k,e]=await Promise.all([request<Progress>('/progress'),request<Lesson[]>('/lessons'),request<Puzzle[]>('/puzzles'),request<Challenge[]>('/challenges'),request<Lab[]>('/sessions'),request<{uygun:boolean;neden?:string}>('/health/capacity'),request<Event[]>('/events')]);
    setProgress(p);setLessons(l);setPuzzles(ps);setChallenges(c);setLabs(s);setCapacity(k);setEvents(e);
  }
  async function action(key:string,run:()=>Promise<void>){if(busy)return;setBusy(key);setError('');try{await run();await refresh();}catch(e){setError(e instanceof Error?e.message:'İşlem başarısız');}finally{setBusy('');}}
  useEffect(()=>{refresh().catch(e=>setError(e.message)).finally(()=>setLoading(false));const timer=setInterval(()=>refresh().catch(()=>{}),15000);return()=>clearInterval(timer);},[]);
  function navigate(value:string){setTab(value);location.hash=value;}
  useEffect(()=>{const change=()=>setTab(location.hash.slice(1)||'ana');addEventListener('hashchange',change);return()=>removeEventListener('hashchange',change);},[]);
  const visibleChallenges=challenges.filter(c=>(labFilter==='hepsi'||(labFilter==='yeni'?c.introduced==='1.1':c.module===labFilter))&&(c.title+' '+c.objective+' '+c.slug).toLocaleLowerCase('tr').includes(labSearch.toLocaleLowerCase('tr')));
  const done=progress.tamamlanan;
  function openLab(slug:string){setTargetLab(slug);setLabFilter('hepsi');setLabSearch('');navigate('lab');}
  function openLesson(slug:string){localStorage.setItem('cyberlab-lesson',slug);navigate('ogretici');}
  const newLessons=lessons.filter(l=>l.introduced==='1.1');
  return <div className="range-shell">
    <a className="skip" href="#main-content">İçeriğe geç</a>
    <aside className="range-sidebar"><a className="brand" href="#ana" onClick={()=>navigate('ana')}><span className="brand-mark">F/</span><span>FLUGEL<small>CYBER RANGE</small></span></a>
      <p className="eyebrow">ÇALIŞMA ALANI</p>
      <nav aria-label="Ana gezinme">{[['ana','Genel bakış','01'],['ogretici','Öğrenme yolu','02'],['bulmaca','Bulmacalar','03'],['lab','Laboratuvar','04']].map(([id,name,n])=><button key={id} aria-current={tab===id?'page':undefined} className={'range-nav '+(tab===id?'active':'')} onClick={()=>navigate(id)}><span>{n}</span>{name}<span className="nav-arrow">↗</span></button>)}</nav>
      <div className="sidebar-bottom"><span className={'status-dot '+(capacity?.uygun?'ready':'')}/>{capacity?.uygun?'Lab servisi hazır':'Lab durumu bekleniyor'}<small>Kişisel eğitim alanı · v1.1</small></div>
    </aside>
    <div className="range-main"><header className="range-top"><span>ÖĞREN / DENE / SAVUN</span><div><span className="level">SEVİYE {progress.level}</span><strong>{progress.xp.toLocaleString('tr-TR')} XP</strong></div></header>
    <main id="main-content" tabIndex={-1}>
      {error&&<div className="error-banner" role="alert">{error}<button onClick={()=>setError('')} aria-label="Uyarıyı kapat">×</button></div>}
      {loading?<p role="status">Çalışma alanı hazırlanıyor…</p>:<>
      {tab==='ana'&&<>
        <div className="hero"><p className="eyebrow">KİŞİSEL SİBER GÜVENLİK LABORATUVARIN</p><h1>Merak et.<br/>Kanıtla. <em>Güvenceye al.</em></h1><p>Bir açığı bulmak başlangıç. Onu kapatıp normal işlevi koruduğunda görev tamamlanır.</p><button className="dugme birincil" onClick={()=>navigate('ogretici')}>Öğrenmeye devam et <span>↗</span></button><div className="hero-grid" aria-hidden="true"><div className="node n1">KEŞİF</div><div className="node n2">KANIT</div><div className="node n3">SAVUNMA</div><div className="node n4">DOĞRULAMA ✓</div></div></div>
        <div className="metrics">{[['Ders',done.filter(x=>x.startsWith('ders:')).length,lessons.length],['Bulmaca',done.filter(x=>x.startsWith('bulmaca:')).length,puzzles.length],['Doğrulanmış lab',done.filter(x=>x.startsWith('lab:')).length,challenges.length],['Günlük seri',progress.streak,'gün']].map(([title,n,total])=><section key={title} className="metric"><span>{title}</span><strong>{n}<small> / {total}</small></strong></section>)}</div>
        <section className="new-collection"><div><p className="eyebrow">YENİ KOLEKSİYON · 1.1</p><h2>{newLessons.length} yeni öğretici, sekiz yeni güvenlik sınırı</h2><p>Web girdisinden C tamsayılarına: önce davranışı tahmin et, sonra kanıtla ve düzelt.</p></div><div className="new-lesson-grid">{newLessons.map(l=><button key={l.slug} onClick={()=>openLesson(l.slug)}><span>{modules[l.module]||l.module} · {l.minutes} dk</span><strong>{l.title}</strong><span>Öğreticiyi aç ↗</span></button>)}</div></section>
        <div className="section-heading"><h2>Bugünün çalışma planı</h2><span>ÜÇ ADIM · TEK ÖĞRENME DÖNGÜSÜ</span></div>
        <div className="izgara">{[['01','Bir kavram öğren','Kısa dersleri takip et, tamamladıklarını kaydet.','ogretici'],['02','Bir bulmacayı çöz','Kanıtı bul; ipucu kullandığında puan etkisini gör.','bulmaca'],['03','Bir savunmayı doğrula','İzole senaryoda keşfet, düzelt ve regresyonu geçir.','lab']].map(([n,title,body,id])=><button key={n} className="plan-card" onClick={()=>navigate(id)}><span>{n} ↗</span><h3>{title}</h3><p>{body}</p></button>)}</div>
        {progress.review.length>0&&<section className="kutu review"><h2>Bugünkü tekrarların</h2>{progress.review.map(r=><p key={r.slug+r.days}>{r.slug.replace(/^[^:]+:/,'')} · {r.days}. gün tekrarı</p>)}</section>}
        <div className="section-heading"><h2>Son etkinlikler</h2><span>FLAG VE KOMUT İÇERİĞİ KAYDEDİLMEZ</span></div>
        <section className="kutu timeline">{events.length?events.slice(0,8).map(e=><div key={e.id}><span>{new Date(e.created_at+'Z'.repeat(e.created_at.endsWith('Z')?0:1)).toLocaleTimeString('tr-TR')}</span><strong>{e.action}</strong><span>{e.result}</span></div>):<p className="soluk">İlk dersini tamamladığında etkinliklerin burada görünür.</p>}</section>
      </>}
      {tab==='ogretici'&&<Lessons lessons={lessons} openLab={openLab} done={done} busy={!!busy} complete={slug=>action('lesson',async()=>{await request('/lessons/'+slug+'/complete',{});})}/>}
      {tab==='bulmaca'&&<Puzzles list={puzzles} done={done} busy={!!busy} action={action}/>}
      {tab==='lab'&&<><div className="section-heading"><div><p className="eyebrow">UYGULAMALI ÖĞRENME</p><h1>Laboratuvar</h1><p className="soluk">Kanıt → flag → savunma → doğrulama. Oturumlar 45 dakika sonra kapanır.</p></div><span className="rozet">{labs.filter(x=>['saglikli','saldiri-tamam'].includes(x.state)).length} / 2 etkin</span></div>
        {!capacity?.uygun&&<p className="uyari-metin">{reasons[capacity?.neden||'runner-yok']||'Kapasite kontrol ediliyor'}</p>}
        <div className="catalog-controls"><label>Lab ara<input className="girdi" value={labSearch} onChange={e=>setLabSearch(e.target.value)} placeholder="JWT, dosya, C…"/></label><label>Koleksiyon<select aria-label="Lab koleksiyonu" value={labFilter} onChange={e=>setLabFilter(e.target.value)}><option value="hepsi">Tüm lablar ({challenges.length})</option><option value="yeni">Yeni eklenenler</option>{[...new Set(challenges.map(c=>c.module))].map(m=><option key={m} value={m}>{modules[m]||m}</option>)}</select></label></div>
        {visibleChallenges.length===0&&<section className="kutu"><p role="status">Bu aramaya uygun lab bulunamadı.</p><button className="dugme" onClick={()=>{setLabSearch('');setLabFilter('hepsi');}}>Tüm labları göster</button></section>}
        <div className="lab-grid">{visibleChallenges.map(c=><LabCard key={c.slug} c={c} selected={c.slug===targetLab} lab={labs.find(l=>l.challenge===c.slug)} done={done} busy={!!busy} action={action}/>)}</div>
      </>}
      </>}
    </main><footer>FLUGEL CYBER RANGE <span>İzole alıştırmalar. Gerçek sistemler hedef değildir.</span></footer></div>
  </div>;
}

function Lessons({lessons,openLab,done,busy,complete}:{lessons:Lesson[];openLab:(slug:string)=>void;done:string[];busy:boolean;complete:(s:string)=>void}){
  const [selected,setSelected]=useState(()=>{const saved=localStorage.getItem('cyberlab-lesson');return lessons.some(l=>l.slug===saved)?saved!:lessons[0]?.slug||'';});
  const [body,setBody]=useState(''),[error,setError]=useState('');
  useEffect(()=>{let alive=true;setBody('');setError('');request<{body:string}>('/lessons/'+selected).then(d=>{if(alive)setBody(d.body);}).catch(e=>{if(alive)setError(e.message);});localStorage.setItem('cyberlab-lesson',selected);return()=>{alive=false;};},[selected]);
  const lesson=lessons.find(l=>l.slug===selected),index=lessons.findIndex(l=>l.slug===selected);
  const locked=lesson?.prerequisites.some(p=>!done.includes('ders:'+p));
  return <><div className="section-heading"><div><p className="eyebrow">TEMELDEN FİNALE</p><h1>Öğrenme yolu</h1></div><span>{lessons.length} ders</span></div><div className="ikili"><aside className="kutu menu" aria-label="Ders seçimi">{lessons.map((d,i)=><button key={d.slug} className={'menu-oge '+(selected===d.slug?'secili':'')} onClick={()=>setSelected(d.slug)}><span className="sira">{done.includes('ders:'+d.slug)?'✓':String(i+1).padStart(2,'0')}</span><span>{d.title} {d.introduced==='1.1'&&<span className="new-badge">YENİ</span>}<small className="soluk">{d.minutes} dakika · {d.module}</small></span></button>)}</aside><article className="kutu lesson-body">{error?<p role="alert">{error}</p>:body?<MarkdownText text={body}/>:<p role="status">Ders yükleniyor…</p>}{locked&&<p className="uyari-metin">Tamamlama için önce: {lesson?.prerequisites.filter(p=>!done.includes('ders:'+p)).join(', ')}</p>}<div className="satir-sag">{lesson?.challenge&&<button className="dugme" onClick={()=>openLab(lesson.challenge!)}>İlgili labı aç ↗</button>}<button className="dugme birincil" disabled={busy||locked||done.includes('ders:'+selected)||!body} onClick={()=>complete(selected)}>{done.includes('ders:'+selected)?'✓ Tamamlandı':'Okudum, tamamla · 50 XP'}</button>{index<lessons.length-1&&<button className="dugme" onClick={()=>setSelected(lessons[index+1].slug)}>Sonraki ders →</button>}</div></article></div></>;
}

type Action=(key:string,run:()=>Promise<void>)=>Promise<void>;
function Puzzles({list,done,busy,action}:{list:Puzzle[];done:string[];busy:boolean;action:Action}){
  const [filter,setFilter]=useState('hepsi'),[search,setSearch]=useState('');
  return <><div className="section-heading"><div><p className="eyebrow">KISA PRATİKLER</p><h1>Bulmacalar</h1></div><label className="search">Ara<input aria-label="Bulmaca ara" value={search} onChange={e=>setSearch(e.target.value)}/></label></div><div className="cipler" role="group" aria-label="Kategori">{['hepsi',...new Set(list.map(p=>p.kategori))].map(k=><button className={'cip '+(filter===k?'secili':'')} key={k} aria-pressed={filter===k} onClick={()=>setFilter(k)}>{categories[k]|| (k==='hepsi'?'Hepsi':k)}</button>)}</div><div className="izgara">{list.filter(p=>(filter==='hepsi'||p.kategori===filter)&&p.baslik.toLocaleLowerCase('tr').includes(search.toLocaleLowerCase('tr'))).map(p=><PuzzleCard key={p.slug} p={p} done={done.includes('bulmaca:'+p.slug)} busy={busy} action={action}/>)}</div></>;
}
function PuzzleCard({p,done,busy,action}:{p:Puzzle;done:boolean;busy:boolean;action:Action}){
  const [answer,setAnswer]=useState(''),[feedback,setFeedback]=useState('');
  async function submit(value:string){await action('answer',async()=>{const r=await request<{dogru:boolean;aciklama:string;xp:number}>('/puzzles/'+p.slug+'/answer',{cevap:value});setFeedback(r.dogru?`Doğru · +${r.xp} XP. ${r.aciklama}`:'Henüz değil. Girdiyi tekrar incele.');});}
  return <section className={'kutu bulmaca '+(done?'bitti':'')}><div className="satir"><span className="rozet">{categories[p.kategori]||p.kategori}</span><span className="soluk">{p.xp} XP</span>{done&&<span className="rozet iyi">✓ Çözüldü</span>}</div><h2>{p.baslik}</h2><MarkdownText text={p.soru}/>{p.cevap_tipi==='secim'?<div className="secenekler">{p.secenekler.map(v=><button key={v} className="secenek" disabled={busy||done} onClick={()=>submit(v)}>{v}</button>)}</div>:<form className="satir" onSubmit={e=>{e.preventDefault();submit(answer);}}><input aria-label={p.baslik+' cevabı'} className="girdi" value={answer} onChange={e=>setAnswer(e.target.value)} disabled={done||busy}/><button className="dugme birincil" disabled={done||busy||!answer.trim()}>Gönder</button></form>}<p role="status">{feedback}</p>{p.ipuclari.map((h,i)=><p className="ipucu" key={i}><strong>İpucu {i+1}:</strong> {h}</p>)}{!done&&p.ipuclari.length<p.ipucu_sayisi&&<button className="dugme" disabled={busy} onClick={()=>action('hint',async()=>{await request('/puzzles/'+p.slug+'/hint',{});})}>İpucu {p.ipuclari.length+1} {p.ipuclari.length===1?'(−%10)':p.ipuclari.length>=2?'(−%25)':'(ücretsiz)'}</button>}</section>;
}
function LabCard({c,selected,lab,done,busy,action}:{c:Challenge;selected:boolean;lab?:Lab;done:string[];busy:boolean;action:Action}){
  const [expanded,setExpanded]=useState(false),[command,setCommand]=useState('help'),[flag,setFlag]=useState(''),[output,setOutput]=useState(''),[feedback,setFeedback]=useState('');
  useEffect(()=>{if(selected)setExpanded(true);},[selected]);
  const active=lab&&['saglikli','saldiri-tamam'].includes(lab.state);
  const locked=c.prerequisites.filter(p=>!done.includes('lab:'+p));
  const minutes=lab?Math.max(0,Math.ceil((Date.parse(lab.expires_at)-Date.now())/60000)):0;
  return <section className={'kutu lab-card '+(expanded?'expanded':'')}><div className="satir"><span className="rozet">{c.module}</span><span className="soluk">{c.score} XP</span>{done.includes('lab:'+c.slug)&&<span className="rozet iyi">✓ Savunma geçti</span>}</div><h2>{c.title} {c.introduced==='1.1'&&<span className="new-badge">YENİ</span>}</h2><p>{c.objective}</p><button className="baglanti" aria-expanded={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?'Ayrıntıyı kapat':'Görevi aç →'}</button>{expanded&&<><p className="guide">{c.guide}</p>{locked.length>0&&<p className="uyari-metin">Önkoşul: {locked.join(', ')}</p>}{active?<><div className="satir lab-status"><span className="rozet iyi">{states[lab.state]}</span><span>{minutes} dk kaldı</span><div className="session-tools">{!lab.extended&&<button className="dugme" disabled={busy} onClick={()=>action('extend',async()=>{await request('/sessions/'+lab.id+'/extend',{});setFeedback('Ek 15 dakika eklendi.');})}>+15 dakika</button>}<button className="dugme" disabled={busy} onClick={()=>action('reset',async()=>{await request('/sessions/'+lab.id+'/reset',{});setOutput('');setFlag('');setFeedback('Önceki lab kapatıldı; yeni oturum ve kanıt oluşturuldu.');})}>Sıfırdan başla</button></div><button className="dugme" disabled={busy} onClick={()=>action('stop',async()=>{await request('/sessions/'+lab.id+'/stop',{});setOutput('Oturum kapatıldı.');})}>Labı durdur</button></div><div className="terminal"><div className="terminal-title">LAB KONSOLU <span>İZİN VERİLEN KOMUTLAR · SHELL DEĞİL</span></div><pre aria-live="polite">{output||'help ile komutları gör. Bu konsol gerçek ağ veya host shell erişimi sağlamaz.'}</pre><form className="console-input" onSubmit={e=>{e.preventDefault();action('command',async()=>{const r=await request<{output:string;exit_code:number}>('/sessions/'+lab.id+'/command',{command});setOutput(prev=>(prev+'\n$ '+command+'\n'+r.output).slice(-22000));});}}><span>$</span><input aria-label={c.title+' lab komutu'} value={command} onChange={e=>setCommand(e.target.value)} autoComplete="off" spellCheck={false} disabled={busy}/><button className="dugme" disabled={busy||!command.trim()}>Çalıştır</button></form></div><form className="satir" onSubmit={e=>{e.preventDefault();action('submit',async()=>{const r=await request<{sonuc:string}>('/sessions/'+lab.id+'/submit',{flag});setFeedback(r.sonuc==='dogru'?'Kanıt doğrulandı. Şimdi patch uygula ve savunmayı doğrula.':r.sonuc==='baska-oturum'?'Bu flag başka bir oturuma ait.':'Flag doğrulanamadı.');});}}><input className="girdi" aria-label={c.title+' flag'} value={flag} onChange={e=>setFlag(e.target.value)} placeholder="FLG{...}" autoComplete="off" disabled={busy}/><button className="dugme" disabled={busy||!flag.trim()}>Kanıtı gönder</button></form><button className="dugme birincil verify" disabled={busy||lab.state!=='saldiri-tamam'} onClick={()=>action('verify',async()=>{const r=await request<{basarili:boolean;output:string;xp:number}>('/sessions/'+lab.id+'/verify',{});setFeedback(r.basarili?`Savunma doğrulandı · +${r.xp} XP. Lab temizlendi.`:'Savunma henüz geçmedi. Test sonuçlarını incele.');setOutput(prev=>prev+'\nDOĞRULAMA\n'+r.output);})}>Savunmayı doğrula →</button></>:<><button className="dugme birincil" disabled={busy||locked.length>0} onClick={()=>action('start',async()=>{const r=await request<Lab>('/sessions',{challenge:c.slug});setOutput('');setFeedback(r.neden?reasons[r.neden]||r.neden:'Lab hazır. help ile başla.');})}>{busy?'İşlem sürüyor…':'Yeni lab başlat · 45 dk'}</button>{lab&&<p>{states[lab.state]||lab.state}</p>}</>}<p role="status">{feedback}</p>{output&&!active&&<pre className="lab-result">{output}</pre>}</>}</section>;
}
