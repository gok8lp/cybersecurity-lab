"""Kaynak eşiği: MemAvailable >= 4 GiB, IO PSI some avg60 < 20, load15 < CPU sayısı. Sağlanmazsa lab başlamaz."""
from __future__ import annotations

import os
from dataclasses import dataclass

ESIK_BELLEK_KB = 4 * 1024 * 1024
ESIK_IO = 20.0


@dataclass(frozen=True)
class Kapasite:
    bellek_kb: int
    io_avg60: float
    load15: float
    cpu: int

    @property
    def uygun(self) -> bool:
        return self.bellek_kb >= ESIK_BELLEK_KB and self.io_avg60 < ESIK_IO and self.load15 < self.cpu

    @property
    def neden(self) -> str | None:
        if self.bellek_kb < ESIK_BELLEK_KB:
            return "bellek-az"
        if self.io_avg60 >= ESIK_IO:
            return "disk-mesgul"
        if self.load15 >= self.cpu:
            return "yuk-yuksek"
        return None

    def ozet(self) -> dict:
        # host ayrıntısı verilmez: yuvarlatılmış değerler
        return {"uygun": self.uygun, "neden": self.neden, "bellek_gb": round(self.bellek_kb / 1048576),
                "yuk": "yuksek" if self.load15 >= self.cpu * 0.75 else "normal"}


def oku(meminfo: str, pressure_io: str, loadavg: str, cpu: int | None = None) -> Kapasite:
    bellek = next(int(l.split()[1]) for l in meminfo.splitlines() if l.startswith("MemAvailable:"))
    some = next(l for l in pressure_io.splitlines() if l.startswith("some "))
    io = float(dict(p.split("=") for p in some.split()[1:])["avg60"])
    return Kapasite(bellek_kb=bellek, io_avg60=io, load15=float(loadavg.split()[2]), cpu=cpu or os.cpu_count() or 1)


def simdi() -> Kapasite:
    with open("/proc/meminfo") as m, open("/proc/pressure/io") as p, open("/proc/loadavg") as l:
        return oku(m.read(), p.read(), l.read())
