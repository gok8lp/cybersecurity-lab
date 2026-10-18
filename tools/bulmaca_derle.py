#!/usr/bin/env python3
"""tests/bulmaca_kaynak.yaml -> content/puzzles.yaml (cevaplar sha256(normalize) özetine çevrilir)."""
import sys
from pathlib import Path

import yaml

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "apps" / "api"))
from cyberlab.puzzles import ozet  # noqa: E402

kaynak = yaml.safe_load((KOK / "tests" / "bulmaca_kaynak.yaml").read_text(encoding="utf-8"))
cikti = []
for b in kaynak:
    kural = b.get("normalize", "kucuk-bosluksuz")
    if b["cevap_tipi"] == "secim" and b["cevap"] not in b["secenekler"]:
        raise SystemExit(f"{b['slug']}: cevap seçeneklerde yok")
    d = {k: v for k, v in b.items() if k != "cevap"}
    d["normalize"] = kural
    d["cevap_ozeti"] = ozet(str(b["cevap"]), kural)
    cikti.append(d)
(KOK / "content" / "puzzles.yaml").write_text(
    "# Üretildi: tools/bulmaca_derle.py — elle düzenleme; kaynak tests/bulmaca_kaynak.yaml\n" +
    yaml.safe_dump(cikti, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"{len(cikti)} bulmaca derlendi")
