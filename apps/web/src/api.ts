export type Ders = { slug: string; module: string; title: string; type: string; minutes: number; prerequisites: string[] };
export type Bulmaca = { slug: string; kategori: string; zorluk: string; baslik: string; soru: string; cevap_tipi: 'metin' | 'secim'; secenekler: string[]; ipuclari: string[]; xp: number };
export type Challenge = { slug: string; module: string; difficulty: string; title: string; type: string; objective: string; score: number };
export type Ilerleme = { xp: number; tamamlanan: string[] };
export type Kapasite = { uygun: boolean; neden: string | null; bellek_gb?: number; yuk?: string };

async function istek<T>(yol: string, govde?: unknown): Promise<T> {
  const r = await fetch(`/api${yol}`, govde === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(govde),
  });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  dersler: () => istek<Ders[]>('/lessons'),
  ders: (slug: string) => istek<{ slug: string; title: string; body: string }>(`/lessons/${slug}`),
  bulmacalar: () => istek<Bulmaca[]>('/puzzles'),
  cevapla: (slug: string, cevap: string) => istek<{ dogru: boolean; aciklama: string | null }>(`/puzzles/${slug}/answer`, { cevap }),
  challengelar: () => istek<Challenge[]>('/challenges'),
  ilerleme: () => istek<Ilerleme>('/progress'),
  kapasite: () => istek<Kapasite>('/health/capacity'),
  oturumAc: (challenge: string) => istek<{ id: string; state: string }>('/sessions', { challenge }),
  gonder: (id: string, flag: string) => istek<{ sonuc: string }>(`/sessions/${id}/submit`, { flag }),
};
