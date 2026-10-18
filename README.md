# FLUGEL Cyber Range

Kişisel siber güvenlik eğitim laboratuvarı: **öğretici dersler**, **tarayıcıda çözülen bulmacalar** ve
**tek kullanımlık, internete kapalı lab görevleri**. Her saldırı görevinin eşlenmiş bir savunma görevi vardır.

> Durum: Faz 1 (güvenli iskelet) tamam. Yerelde çalışıyor; sunucuya henüz kurulmadı.

## İçindekiler

- [Ne var?](#ne-var)
- [Hızlı başlangıç (yerel)](#hızlı-başlangıç-yerel)
- [Nasıl kullanılır](#nasıl-kullanılır)
- [Mimari](#mimari)
- [Güvenlik sınırları](#güvenlik-sınırları)
- [İçerik ekleme](#içerik-ekleme)
- [Testler](#testler)
- [Yol haritası](#yol-haritası)

## Ne var?

| Bölüm | İçerik |
|---|---|
| Öğretici | 5 ders: Başlarken, Kapsam ve etik, Linux izinleri, Kodlama/şifreleme/özet, HTTP ve güvenlik başlıkları |
| Bulmacalar | 12 bulmaca, 5 kategori: kodlama, özet (hash), dosya izinleri, HTTP, güvenli kod |
| Lablar | `linux-permission-leak` (fazla izinli yedek: saldırı + savunma), `scope-guard` (kapsam koruması) |
| Puan | XP, tamamlanan bulmacalar; ipucu kademeleri (2. ipucu −%10, 3. ipucu −%25) |

## Hızlı başlangıç (yerel)

Gereken: Python 3.12+, Node 20+. Lab konteynerleri için Docker (bu PC'de yok; sunucuda var).

```bash
cd ~/Projects/flugel-cyber-lab
python3 -m venv .venv
.venv/bin/pip install fastapi==0.115.6 uvicorn==0.34.0 sqlmodel==0.0.22 pyyaml==6.0.2 pytest==8.3.4 httpx==0.28.1
```

API:

```bash
CYBERLAB_AUTO=1 CYBERLAB_DATA=./data PYTHONPATH=apps/api .venv/bin/uvicorn cyberlab.main:app --host 127.0.0.1 --port 8000
```

Arayüz (ayrı terminal):

```bash
cd apps/web && npm install && npx vite --host 127.0.0.1 --port 5173
```

Tarayıcıda: <http://127.0.0.1:5173>

## Nasıl kullanılır

1. **Ana sayfa:** "Bugünün üçlüsü" (1 ders, 1 bulmaca, 1 lab), ilerleme ve lab durumu.
2. **Öğretici:** dersler sırayla; her dersin sonunda "Sonraki ders". Önce *Başlarken* ve *Kapsam ve etik* okunmalı.
3. **Bulmacalar:** kategoriye göre süz; cevabı yaz ya da seçeneği seç. Takılırsan ipuçlarını sırayla aç.
   Doğru cevaptan sonra kısa bir açıklama çıkar ve XP eklenir (aynı bulmaca ikinci kez XP vermez).
4. **Lablar:** "Lab başlat" sana özel, internete kapalı bir hedef açar. Bulduğun `FLG{...}` değerini gönder,
   ardından savunma adımında açığı kapat. Lab servisi (runner) çalışmıyorsa ya da sunucu meşgulse neden yazılır.

## Mimari

```text
tarayıcı ── React (apps/web) ── /api ── FastAPI (apps/api)
                                           │  SQLite (data/cyberlab.db), içerik (content/)
                                           └── runner (Unix soket, yalnız izin listesi)
                                                  └── docker compose: labs/<görev>/compose.yaml
                                                       (internal ağ, tek kullanımlık)
```

| Dizin | Görev |
|---|---|
| `apps/api/cyberlab/` | `main.py` uç noktalar, `content.py` ders/görev yükleyici, `puzzles.py` bulmaca motoru, `flags.py` oturum bayrağı, `models.py` veri modeli |
| `apps/web/src/` | `Uygulama.tsx` sekmeler, `api.ts` istemci, `stil.css` koyu tema |
| `runner/` | `kapsam.py` hedef koruması, `kapasite.py` kaynak eşiği, `runner.py` başlat/durdur |
| `content/` | `lessons/*.md` dersler, `challenges.yaml` görevler, `puzzles.yaml` (üretilir) |
| `labs/<görev>/` | Dockerfile, `compose.yaml`, doğrulayıcı |
| `tests/` | API, runner ve güvenlik politikası testleri; `bulmaca_kaynak.yaml` |
| `tools/` | `bulmaca_derle.py` |
| `docs/` | Codex'in tasarım belgeleri (MASTER_SPEC, CURRICULUM, CLAUDE_BUILD_ORDER) |

## Güvenlik sınırları

- Gerçek ev sunucusu, ev ağı, modem, Cloudflare, VM'ler ve üretim konteynerleri **asla hedef değildir**.
- Lab ağları `internal: true`: internete ve ev ağına çıkamaz. Hedef portları hiçbir yere yayımlanmaz.
- Her lab konteyneri: salt okunur kök, `cap_drop: [ALL]`, `no-new-privileges`, bellek/CPU/süreç sınırı, sağlık kontrolü.
- `privileged`, `network_mode: host`, host PID/IPC, `docker.sock` ve host dizini bağlamak yasak; testler bunu denetler.
- API Docker'a dokunmaz; yalnız runner, izin listesindeki görevleri `docker compose` argv ile açar (shell yok).
- Runner, sunucuda boş bellek < 4 GiB, disk baskısı ≥ %20 ya da yük yüksekse lab başlatmaz.
- Bayraklar imajda yok: oturum başında HMAC ile üretilir, veritabanında yalnız özeti tutulur; başka oturumda geçmez.
- Bulmaca cevapları içerikte açık değil: `sha256(normalize(cevap))`.

## İçerik ekleme

**Ders:** `content/lessons/NN-ad.md` dosyası, başında ön bilgi bloğu:

```markdown
---
slug: yeni-ders
module: web
title: Başlık
type: theory
minutes: 10
prerequisites: [baslarken]
---
# İçerik (Markdown)
```

Önkoşul döngüsü ya da bilinmeyen önkoşul yükleme hatası verir.

**Bulmaca:** `tests/bulmaca_kaynak.yaml` dosyasına ekle (cevap burada açık), sonra:

```bash
.venv/bin/python tools/bulmaca_derle.py
```

Bu komut `content/puzzles.yaml` dosyasını cevap özetleriyle yeniden üretir.

**Lab görevi:** `content/challenges.yaml` kaydı + `labs/<slug>/compose.yaml` (güvenlik testlerinden geçmeli).

## Testler

```bash
.venv/bin/python -m pytest -q
cd apps/web && npx tsc -b && npx vite build
```

20 test: API (bayrak tekrar kullanımı, bulmaca cevapları, XP), runner (kapsam dışı hedef reddi, kapasite eşiği,
izin listesi, argv), güvenlik politikası (yasaklı ayarlar, lab sertleştirme).

## Yol haritası

| Faz | Durum |
|---|---|
| 0 Keşif | tamam |
| 1 Güvenli iskelet | tamam |
| 2 İçerik ve puan motoru (12 ders, aralıklı tekrar) | kısmen: 5 ders, 12 bulmaca |
| 3 Runner (Unix soket servisi, 20 döngü testi) | iskelet |
| 4 İlk dört görev | 1/4 (`linux-permission-leak` dosyaları hazır, sunucuda denenmedi) |
| 5 C/C++ yolu | bekliyor |
| 6 Tarayıcı terminali, erişilebilirlik | bekliyor |
| 7 Sunucuya kurulum | kullanıcı onayı bekler (port, alan adı, erişim politikası gösterilecek) |
