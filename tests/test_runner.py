import pytest

from runner import kapasite, kapsam, runner


@pytest.mark.parametrize("hedef", ["192.168.0.15", "192.168.1.1", "10.0.0.1", "172.17.0.1", "100.86.88.1",
                                   "127.0.0.1", "169.254.1.1", "8.8.8.8", "example.com", "gokalpgoksu.com", "::1"])
def test_kapsam_disi_reddedilir(hedef):
    assert not kapsam.hedef_izinli(hedef)


def test_oturum_agi_icindeki_hedef_kabul():
    assert kapsam.hedef_izinli("10.213.4.3", "10.213.4.0/28")
    assert not kapsam.hedef_izinli("10.213.5.3", "10.213.4.0/28")
    assert kapsam.hedef_izinli("target-linux-perm")
    assert not kapsam.hedef_izinli("10.213.4.3", "192.168.0.0/24")  # lab bloğu dışında ağ verilemez


def test_kapasite_esigi():
    mem = "MemTotal: 16000000 kB\nMemAvailable: 5000000 kB\n"
    io_iyi = "some avg10=1.0 avg60=5.0 avg300=3.0 total=1\nfull avg10=0 avg60=0 avg300=0 total=0\n"
    io_kotu = "some avg10=80 avg60=45.0 avg300=30 total=1\n"
    assert kapasite.oku(mem, io_iyi, "1.0 1.0 2.0 1/1 1", cpu=12).uygun
    k = kapasite.oku(mem, io_kotu, "1.0 1.0 2.0 1/1 1", cpu=12)
    assert not k.uygun and k.neden == "disk-mesgul"
    az = kapasite.oku("MemAvailable: 1000000 kB\n", io_iyi, "1 1 1 1/1 1", cpu=12)
    assert az.neden == "bellek-az"
    assert kapasite.oku(mem, io_iyi, "30 30 30 1/1 1", cpu=12).neden == "yuk-yuksek"


def test_izin_listesi_ve_argv():
    izin = runner.izin_listesi()
    assert "linux-permission-leak" in izin
    assert "scope-guard" not in izin  # lab konteyneri yok
    argv = runner.baslat_argv("linux-permission-leak", "a1b2c3d4e5f6")
    assert argv[:4] == ["docker", "compose", "-p", "cyberlab-a1b2c3d4e5f6"]
    assert all(";" not in a and "&&" not in a for a in argv)
    with pytest.raises(PermissionError):
        runner.baslat_argv("rm -rf /", "a1b2c3d4e5f6")
    with pytest.raises(ValueError):
        runner.baslat_argv("linux-permission-leak", "../../x")
