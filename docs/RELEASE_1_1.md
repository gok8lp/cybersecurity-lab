# FLUGEL Cyber Range 1.1 — Genişletilmiş öğreticiler

1.0 üzerine **8 ders ve 8 lab** eklendi. Toplam: **20 ders, 17 bulmaca, 21 lab**.

| Yeni öğretici | Lab | Gerçekleştirme |
|---|---|---|
| XSS ve çıktı bağlamı | web-output-encoding | Gerçek HTML parser; etkin etiket ile kodlanmış metni karşılaştırır. Tarayıcıda JS yürütmez. |
| Dosya yolu sınırı | path-traversal | Gerçek geçici public/private dosyaları; Path.resolve ve bileşen tabanlı kök kontrolü. |
| CSRF ve oturum | csrf-token | Oturuma bağlı token doğrulama fonksiyonu; gerçek hesap veya HTTP isteği yok. |
| JWT imzası | jwt-signature | Gerçek base64url ve HMAC; none, geçerli HS256 ve değiştirilmiş payload testleri. Üretim JWT kütüphanesi değil. |
| Parola saklama | password-storage | Küçük eğitim sözlüğü ve SHA-256 karşılaştırması; rastgele salt, gerçek scrypt, doğru/yanlış parola testleri. |
| Güvenli arşiv açma | archive-slip | Gerçek ZIP üyelerinin elle çıkarılması; kök dışı üyeyi reddeder, normal arşivi açar. |
| C tamsayıları | c-integer-boundary | gcc -Wall -Wextra -Werror; 256 daraltmasını reddeder, 4 girdisini kabul eder. Bellek dışına yazmaz. |
| Binary ve sırlar | binary-secret | Gerçek gcc + strings; eğitim sabitini binary dışında tutma, eksik secretı reddetme. |

Her ders kavram, keşif, kaynak örneği, savunma, regresyon ve kontrol sorusu içerir. Yeni koleksiyon ana ekranda görünür; derslerden ilgili laba geçilir. Lab listesinde metin arama, modül ve yeni eklenenler filtresi vardır.

## Oturum araçları

- Bir kez +15 dakika: özel runner sicilinde idempotent olarak uzatılır; API yeniden denemesi ek süreyi iki kere vermez.
- Sıfırdan başla: önce eski proje temizlenir, sonra yeni kimlik ve HMAC flag ile oturum açılır. Eski kanıt yeni oturumda geçmez. Kapasite yoksa eski oturum kapalı kalır ve arayüz sebebi gösterir.
- İlerleme korunur. Yeni SessionDetail tablosu SQLModel create_all ile eklenir; mevcut tabloların kolonları değiştirilmez. Güncelleme öncesi SQLite online yedeği alınmalıdır.

## Kurulum

1.0 kurulum ve işletim adımları [RELEASE_1_0.md](RELEASE_1_0.md) içinde geçerlidir. 1.1 hedef imajı `flugel-cyberlab/exercises:1.1`; önceki imaj korunur. `deploy/install.sh`, hazırlanmış dist dahil release klasöründen çalıştırılır. Servis yalnız 127.0.0.1:8317 dinler.

## Kapsam

Konsol halen eğitim komutları ve hazır savunmalarla çalışır; serbest attacker shell değildir. Yeni parser/crypto/dosya/derleme alıştırmaları doğrudan kendi geçici fixture'larını sınar. Gerçek web hesabı veya LAN hedefi kullanılmaz. 1.0'ın sentetik senaryoları bu güncellemede gerçek web servisine dönüşmüş sayılmaz.

Tam ürün şartnamesindeki açık işler [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) içinde izlenir. Mevcut genişletme bütün şartnamenin tamamlandığı iddiası değildir.

## 27 Ekim 2026 doğrulama kaydı

- Linux'ta 95 Python testi geçti; Windows'ta 92 geçti, POSIX/derleyici gerektiren 3 test Linux'ta doğrulandı.
- 21 gerçek Docker oturumunda kanıt, yanlış savunmanın reddi, doğru savunma ve temizleme geçti.
- 20 ardışık başlat/uzat/sıfırla/durdur çevrimi geçti. İkinci uzatma reddedildi, eski flag yeni oturumda çalışmadı. Sonunda managed container/network/volume sayısı sıfır.
- Üç otomatik Playwright testi: yeni ders-lab bağlantısı, yeni filtre/JWT arama/boş sonuç, 1366px ve 390px klavye/taşma/axe WCAG kontrolü geçti.
- Kontrast ve kaydırılan kod bloklarının klavye odağı düzeltildi. CI tarayıcı testini Python + frontend build sonrasında çalıştırır.
- Sunucu release'i /opt/flugel-cyberlab/releases/20261027T175848Z; SQLite online yedeği güncellemeden önce alınıp integrity_check ile doğrulandı. Kullanıcı XP'si kabul testlerinden etkilenmedi.

Yerel tarayıcı testi: `cd apps/web && pnpm exec playwright install chromium && pnpm run test:browser`. Python PATH'te değilse CYBERLAB_PYTHON ortam değişkenini venv python yürütülebilirinin mutlak yoluna ayarlayın. Testler üretim 8317 yerine ayrı 8318 portu ve geçici veri dizini kullanır.
