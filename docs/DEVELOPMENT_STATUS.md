# Şartnameye göre kalan işler

Kullanıcının amacı kapsamlı ve bitmiş bir eğitim platformudur. Bu liste mevcut sürümü şartnameye göre izler; eksik maddeler mevcut testlerin yeşil olmasıyla tamamlanmış sayılmaz.

| Gereksinim | Durum / gereken kanıt |
|---|---|
| 12+ ders, saldırı + savunma, 13'ten fazla öğretici lab | 20 ders ve 21 lab. Linux'ta 95 test, 21 senaryonun Docker kabulü ve 20 yaşam döngüsü geçti; ayrıntılar RELEASE_1_1.md içinde. |
| Önkoşullar, kalıcı ilerleme, flag ayrımı, puan tekilliği | API testleri var; gerçek kullanıcı verisi güncellemelerde korunmalı. |
| Start/reset/stop, TTL ve tek +15 dakika | 1.1 uygulandı: 20 gerçek start/extend/reset/stop çevrimi geçti. Eski oturum flag'i yeni oturumda reddedildi; sıfır artık managed kaynak. |
| Gerçek 8 MVP hedefi + attacker/verifier ayrımı | Eksik. Bazı eski senaryolar sentetik, konsol sınırlı komutlar kullanıyor. Gerçek HTTP hedefleri, ayrı attacker ve bağımsız verifier gerekiyor. |
| İnternetsiz, host ve LAN'a erişmeyen attacker terminali | Eksik. Gelecekteki shell için ağ/host sınırı doğrudan egress testleriyle kanıtlanmalı. |
| C kaynak düzenleme, gdb/objdump ve normal/sınır testleri | Kısmi: hazır kaynaklar derleniyor; serbest düzenleme ve tam araç yolu eksik. |
| Üç kademeli lab ipucu, kalıcı rapor ve tekrar tamamlama | Eksik. Mevcut bulmaca ipuçları var; lab katmanı ve tekrar ekranı gerekli. |
| Modül haritası, ayrı red/blue puan, deterministik rozetler | Eksik. Genel XP ve ders önkoşulları var. |
| Hazırlanıyor/sıfırlanıyor durumları, uzaktan işlem takibi | Kısmi: uzun istek boyunca bekleniyor; kalıcı iş takibi gerekli. |
| Migration ve yedek/geri yükleme yolu | Kısmi: 1.1 yalnız ek tablo. Sürümlü migration ve gerçek veriyle restore/rollback testi gerekli. |
| CI erişilebilirlik testi | Playwright + axe eklendi: yeni koleksiyon/gezinme/arama ve 1366/390px WCAG + klavye testleri yerelde geçti. CI aynı testleri çalıştırır; son Actions sonucu ayrıca doğrulanmalı. |
| 12 haftalık tam eğitim yolu ve final rapor kalitesi | Kısmi: dersler ve yeni uzmanlaşma modülleri var. Haftalık eşleme ve final rapor rubriği geliştirilmeli. |
| Deployment ve gözlem | Loopback/SSH + ayrı servis hesapları kurulu. Güncellemeler yedek, sağlık ve temiz kaynak kontrolüyle sürdürülmeli. Public yayın isteğe bağlı; şu an talep edilmedi. |
