import { useEffect, useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api, Bulmaca, Challenge, Ders, Ilerleme, Kapasite } from './api';

type Sekme = 'ana' | 'ogretici' | 'bulmaca' | 'lab';
const SEKMELER: [Sekme, string][] = [['ana', 'Ana sayfa'], ['ogretici', 'Öğretici'], ['bulmaca', 'Bulmacalar'], ['lab', 'Lablar']];
const KATEGORI: Record<string, string> = { kodlama: 'Kodlama', ozet: 'Özet (hash)', izinler: 'Dosya izinleri', http: 'HTTP', 'guvenli-kod': 'Güvenli kod' };
const NEDEN: Record<string, string> = { 'bellek-az': 'Sunucuda yeterli boş bellek yok', 'disk-mesgul': 'Sunucunun diski meşgul', 'yuk-yuksek': 'Sunucu yükü yüksek', 'runner-yok': 'Lab servisi (runner) çalışmıyor' };

export function Uygulama() {
  const [sekme, setSekme] = useState<Sekme>('ana');
  const [ilerleme, setIlerleme] = useState<Ilerleme>({ xp: 0, tamamlanan: [] });
  const yenile = () => api.ilerleme().then(setIlerleme).catch(() => {});
  useEffect(() => { yenile(); }, []);
  return (
    <div className="sayfa">
      <header className="ust">
        <div><h1>Siber Güvenlik Laboratuvarı</h1><p className="soluk">Saldırıyı ve savunmayı birlikte öğren</p></div>
        <div className="xp" aria-label={`${ilerleme.xp} XP`}>{ilerleme.xp} XP</div>
      </header>
      <nav className="sekmeler" aria-label="Bölümler">
        {SEKMELER.map(([id, ad]) => (
          <button key={id} className={sekme === id ? 'sekme secili' : 'sekme'} aria-current={sekme === id ? 'page' : undefined} onClick={() => setSekme(id)}>{ad}</button>
        ))}
      </nav>
      <main>
        {sekme === 'ana' && <Ana ilerleme={ilerleme} git={setSekme} />}
        {sekme === 'ogretici' && <Ogretici />}
        {sekme === 'bulmaca' && <Bulmacalar tamam={ilerleme.tamamlanan} degisti={yenile} />}
        {sekme === 'lab' && <Lablar />}
      </main>
    </div>
  );
}

function Ana({ ilerleme, git }: { ilerleme: Ilerleme; git: (s: Sekme) => void }) {
  const [kap, setKap] = useState<Kapasite | null>(null);
  const [toplam, setToplam] = useState(0);
  useEffect(() => { api.kapasite().then(setKap).catch(() => {}); api.bulmacalar().then(b => setToplam(b.length)).catch(() => {}); }, []);
  const cozulen = ilerleme.tamamlanan.filter(s => s.startsWith('bulmaca:')).length;
  return (
    <div className="izgara">
      <section className="kutu">
        <h2>Bugünün üçlüsü</h2>
        <ol className="liste">
          <li><button className="baglanti" onClick={() => git('ogretici')}>1 ders oku</button></li>
          <li><button className="baglanti" onClick={() => git('bulmaca')}>1 bulmaca çöz</button></li>
          <li><button className="baglanti" onClick={() => git('lab')}>1 lab görevi dene</button></li>
        </ol>
      </section>
      <section className="kutu">
        <h2>İlerleme</h2>
        <p className="buyuk">{cozulen} / {toplam}</p>
        <p className="soluk">çözülen bulmaca</p>
        <div className="cubuk" role="progressbar" aria-valuemin={0} aria-valuemax={toplam} aria-valuenow={cozulen}><span style={{ width: `${toplam ? (cozulen / toplam) * 100 : 0}%` }} /></div>
      </section>
      <section className="kutu">
        <h2>Laboratuvar</h2>
        {kap === null ? <p className="soluk">Durum alınıyor…</p> : kap.uygun
          ? <p><span className="rozet iyi">Hazır</span> yeni lab başlatılabilir.</p>
          : <p><span className="rozet uyari">Bekliyor</span> {NEDEN[kap.neden ?? ''] ?? 'Şu an lab başlatılamıyor'}.</p>}
      </section>
    </div>
  );
}

function Ogretici() {
  const [dersler, setDersler] = useState<Ders[]>([]);
  const [secili, setSecili] = useState<string | null>(null);
  const [icerik, setIcerik] = useState<{ title: string; body: string } | null>(null);
  useEffect(() => { api.dersler().then(d => { setDersler(d); setSecili(d[0]?.slug ?? null); }).catch(() => {}); }, []);
  useEffect(() => { if (secili) api.ders(secili).then(setIcerik).catch(() => setIcerik(null)); }, [secili]);
  const sira = dersler.findIndex(d => d.slug === secili);
  return (
    <div className="ikili">
      <aside className="kutu menu" aria-label="Dersler">
        {dersler.map((d, i) => (
          <button key={d.slug} className={d.slug === secili ? 'menu-oge secili' : 'menu-oge'} onClick={() => setSecili(d.slug)}>
            <span className="sira">{i + 1}</span><span>{d.title}<small className="soluk">{d.minutes} dk</small></span>
          </button>
        ))}
      </aside>
      <article className="kutu metin">
        {icerik ? <Markdown remarkPlugins={[remarkGfm]}>{icerik.body}</Markdown> : <p className="soluk">Ders yükleniyor…</p>}
        <div className="satir-sag">
          {sira > 0 && <button className="dugme" onClick={() => setSecili(dersler[sira - 1].slug)}>Önceki</button>}
          {sira >= 0 && sira < dersler.length - 1 && <button className="dugme birincil" onClick={() => setSecili(dersler[sira + 1].slug)}>Sonraki ders</button>}
        </div>
      </article>
    </div>
  );
}

function Bulmacalar({ tamam, degisti }: { tamam: string[]; degisti: () => void }) {
  const [liste, setListe] = useState<Bulmaca[]>([]);
  const [kategori, setKategori] = useState('hepsi');
  useEffect(() => { api.bulmacalar().then(setListe).catch(() => {}); }, []);
  const kategoriler = ['hepsi', ...Array.from(new Set(liste.map(b => b.kategori)))];
  return (
    <div>
      <div className="cipler" role="group" aria-label="Kategori">
        {kategoriler.map(k => <button key={k} className={k === kategori ? 'cip secili' : 'cip'} aria-pressed={k === kategori} onClick={() => setKategori(k)}>{k === 'hepsi' ? 'Hepsi' : KATEGORI[k] ?? k}</button>)}
      </div>
      <div className="izgara">
        {liste.filter(b => kategori === 'hepsi' || b.kategori === kategori).map(b => (
          <BulmacaKarti key={b.slug} b={b} cozuldu={tamam.includes(`bulmaca:${b.slug}`)} degisti={degisti} />
        ))}
      </div>
    </div>
  );
}

function BulmacaKarti({ b, cozuldu, degisti }: { b: Bulmaca; cozuldu: boolean; degisti: () => void }) {
  const [cevap, setCevap] = useState('');
  const [ipucu, setIpucu] = useState(0);
  const [sonuc, setSonuc] = useState<{ dogru: boolean; aciklama: string | null } | null>(null);
  const gonder = async (deger: string) => {
    if (!deger.trim()) return;
    const s = await api.cevapla(b.slug, deger);
    setSonuc(s);
    if (s.dogru) degisti();
  };
  const bitti = cozuldu || sonuc?.dogru;
  return (
    <section className={bitti ? 'kutu bulmaca bitti' : 'kutu bulmaca'}>
      <div className="satir">
        <span className="rozet">{KATEGORI[b.kategori] ?? b.kategori}</span>
        <span className="soluk">{b.zorluk} · {b.xp} XP</span>
        {bitti && <span className="rozet iyi">Çözüldü</span>}
      </div>
      <h3>{b.baslik}</h3>
      <div className="metin"><Markdown remarkPlugins={[remarkGfm]}>{b.soru}</Markdown></div>
      {b.cevap_tipi === 'secim' ? (
        <div className="secenekler" role="group" aria-label="Seçenekler">
          {b.secenekler.map(s => <button key={s} className="secenek" disabled={!!bitti} onClick={() => gonder(s)}><code>{s}</code></button>)}
        </div>
      ) : (
        <form className="satir" onSubmit={e => { e.preventDefault(); gonder(cevap); }}>
          <label className="gizli" htmlFor={`c-${b.slug}`}>Cevap</label>
          <input id={`c-${b.slug}`} className="girdi" value={cevap} disabled={!!bitti} onChange={e => setCevap(e.target.value)} placeholder="Cevabın" autoComplete="off" />
          <button className="dugme birincil" disabled={!!bitti}>Gönder</button>
        </form>
      )}
      {sonuc && !sonuc.dogru && <p className="uyari-metin" role="status">Olmadı, bir daha dene.</p>}
      {sonuc?.dogru && sonuc.aciklama && <p className="iyi-metin" role="status">{sonuc.aciklama}</p>}
      {!bitti && b.ipuclari.length > 0 && (
        <div className="ipuclari">
          {b.ipuclari.slice(0, ipucu).map((i, n) => <p key={n} className="ipucu"><strong>İpucu {n + 1}:</strong> {i}</p>)}
          {ipucu < b.ipuclari.length && <button className="dugme" onClick={() => setIpucu(ipucu + 1)}>İpucu {ipucu + 1}{ipucu === 1 ? ' (−%10)' : ipucu === 2 ? ' (−%25)' : ''}</button>}
        </div>
      )}
    </section>
  );
}

function Lablar() {
  const [liste, setListe] = useState<Challenge[]>([]);
  const [oturum, setOturum] = useState<Record<string, { id: string; state: string }>>({});
  const [flag, setFlag] = useState<Record<string, string>>({});
  const [sonuc, setSonuc] = useState<Record<string, string>>({});
  useEffect(() => { api.challengelar().then(setListe).catch(() => {}); }, []);
  const ac = async (slug: string) => setOturum({ ...oturum, [slug]: await api.oturumAc(slug) });
  const DURUM: Record<string, string> = { saglikli: 'Hazır', kuyrukta: 'Kuyrukta: sunucu meşgul', 'runner-yok': 'Lab servisi henüz kurulmadı', hata: 'Başlatılamadı', hazirlaniyor: 'Hazırlanıyor' };
  return (
    <div className="izgara">
      {liste.map(c => (
        <section key={c.slug} className="kutu">
          <div className="satir"><span className="rozet">{c.module}</span><span className="soluk">{c.difficulty} · {c.score} XP</span></div>
          <h3>{c.title}</h3>
          <p>{c.objective}</p>
          {!oturum[c.slug] ? <button className="dugme birincil" onClick={() => ac(c.slug)}>Lab başlat</button> : (
            <>
              <p><span className={oturum[c.slug].state === 'saglikli' ? 'rozet iyi' : 'rozet uyari'}>{DURUM[oturum[c.slug].state] ?? oturum[c.slug].state}</span></p>
              <form className="satir" onSubmit={async e => { e.preventDefault(); setSonuc({ ...sonuc, [c.slug]: (await api.gonder(oturum[c.slug].id, flag[c.slug] ?? '')).sonuc }); }}>
                <label className="gizli" htmlFor={`f-${c.slug}`}>Flag</label>
                <input id={`f-${c.slug}`} className="girdi" placeholder="FLG{...}" value={flag[c.slug] ?? ''} onChange={e => setFlag({ ...flag, [c.slug]: e.target.value })} autoComplete="off" />
                <button className="dugme birincil">Gönder</button>
              </form>
              {sonuc[c.slug] && <p role="status" className={sonuc[c.slug] === 'dogru' ? 'iyi-metin' : 'uyari-metin'}>{sonuc[c.slug] === 'dogru' ? 'Doğru! Şimdi savunma adımına geç.' : sonuc[c.slug] === 'baska-oturum' ? 'Bu flag başka bir oturuma ait.' : 'Yanlış flag.'}</p>}
            </>
          )}
        </section>
      ))}
    </div>
  );
}
