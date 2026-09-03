İSU 185 TALEP TAKİP — TAM PROJE

KURULUM
1. ZIP'i çıkar.
2. VS Code ile ISU_185_TAM_PROJE_FINAL klasörünü aç.
3. Trust this folder.
4. Terminal: .\KURULUM_TEK_TIK.bat
5. Kurulum sonunda sistem yöneticisi hesabını oluştur.
6. Sonraki açılışlarda .\BASLAT.bat
7. http://127.0.0.1:8000/giris/

İÇERİK
- Profesyonel özel sistem paneli (Django Admin'e gitmez)
- 185 çağrı ekranı
- İlçe → mahalle → yol bağı
- İş türü → iş alt türü bağı
- Leaflet + OpenStreetMap
- Seçilen adresi haritada bulma
- Marker elle düzeltme
- Parent / child rol modeli
- Data-driven rol atama kuralları
- İlçe + iş türüne göre otomatik koordinatör bulma
- Aynı ilçe + rol kuralı + uzmanlık + müsaitlik ile saha filtreleme
- Her ilçe için koordinatörleri otomatik hesap oluşturma
- Her ilçe için ortak saha hesaplarını otomatik oluşturma
- 185 → koordinatör → saha → tamamlandı akışı
- Ortak geri bildirim zaman çizelgesi
- Her ekranda açılır işlem logu
- Sistem arıza haritası: bekleyen kırmızı, işlemde turuncu, tamamlanan yeşil
- Talep filtreleri
- Raporlar ve CSV dışa aktarma
- İş türü / alt türü yönetimi
- Adres CSV içe aktarma
- PostgreSQL'e geçiş desteği

ADRES ANA VERİSİ
Kocaeli'nin 12 ilçesi hazırdır. Sistem hemen test edilebilsin diye küçük bir demo
mahalle/yol seti de vardır. Tam güncel kurumsal mahalle-cadde-sokak ana verisi
harici veridir ve Sistem > Adres Yönetimi ekranından CSV ile tek seferde yüklenir.

CSV:
ilce,mahalle,yol,tur,lat,lng

POSTGRESQL
Varsayılan SQLite'tır. PostgreSQL için ortam değişkenleri:
ISU_DB_ENGINE=postgresql
ISU_DB_NAME=isu185
ISU_DB_USER=postgres
ISU_DB_PASSWORD=...
ISU_DB_HOST=localhost
ISU_DB_PORT=5432


V2 GÜNCELLEMELERİ
- İş türleri 8 ana kategoriye genişletildi:
  İçme Suyu, Kanalizasyon, Yağmur Suyu, Vidanjör ve Kanal Açma,
  Elektromekanik, Teknik İnceleme, Abone İşleri, Yol ve Kazı Onarım.
- Her ana tür için kapsamlı iş alt türleri eklendi.
- Cadde/sokak dış kaynaktan bulunamazsa 185 personeli gerçek yol adını manuel yazabilir.
  Manuel girilen yol seçilen mahallenin altında veritabanına kaydolur ve sonraki taleplerde listelenir.
- Koordinatör paneli zenginleştirildi:
  bölge haritası, atama bekleyen talepler, saha ekip müsaitliği,
  son geri bildirimler, yetki/uzmanlık etiketleri ve detaylı talep tablosu.
- Parent/child ve data-driven rol/ilçe algoritması değiştirilmedi.

MEVCUT V1 PROJESİNİ GÜNCELLEME
V2 dosyalarını mevcut proje klasörünüzün üstüne kopyalarsanız db.sqlite3 silinmez.
Ardından GUNCELLE_V2.bat çalıştırın.


V3 — GERÇEK MAHALLE VERİSİ
- Mahalle listesi artık OpenStreetMap'ten tahmin edilmez.
- Kocaeli ilçeleri TürkiyeAPI v2'nin 2025 idari veri seti ile eşleştirilir.
- API'den gelen mahalleler yerel SQLite/PostgreSQL veritabanına kaydedilir.
- Senkron başarılı olduğunda o ilçedeki eski/demo mahalle kayıtları silinmez,
  geçmiş talepler bozulmasın diye pasife alınır.
- Sistem internet/API geçici olarak yoksa daha önce senkronlanan yerel mahalle
  verisiyle çalışmaya devam eder.
- Cadde/sokak için OSM araması devam eder; bulunamazsa V2'deki manuel yol girişi
  sayesinde talep kaydı engellenmez.


V4 — SAHA ATAMA MİMARİSİ
- Saha rolleri İSU'nun kamuya açık güncel hizmet alanlarıyla uyumlu operasyon
  kategorilerine ayrıldı.
- Sistem Yönetimi > Kullanıcılar ekranında "Tüm İlçe Saha Ekipleri" butonu vardır.
- Bu buton aktif tüm ilçelerde eksik saha hesaplarını otomatik oluşturur.
- Her uzman saha hesabına ilgili İş Türü uzmanlığı otomatik atanır.
- Ortak İlçe Saha uzmanlık listesi boş bırakılır ve genel fallback ekip görevi görür.
- Sistem rol/ilçe/aktiflik/müsaitlik/uzmanlık kurallarına uyan saha hesaplarını listeler.
- Şef/koordinatör bu listeden ilgili saha ekibini MANUEL seçerek atar.
- Otomatik saha önerisi, puanlama veya otomatik atama yoktur.
- Yeni İş Türleri: Kaçak Su ve Su Kayıpları; Su Kalitesi ve Kirlilik.


V5 FINAL — 185 FORM VE OTOMATİK HAREKET AKIŞI
- Talep başarıyla kaydedilince detay sayfasına otomatik yönlendirme kaldırıldı.
- POST/Redirect/GET kullanıldığı için kayıt sonrası 185 formu otomatik temizlenir.
- 185 ekranına Yeni Talep / Talepler sekmeleri eklendi.
- Talep detay sayfası yalnız Talepler gridindeki Detay bağlantısından açılır.
- Manuel Geri Bildirim Gönder formu tamamen kaldırıldı.
- Tek bir salt-okunur Otomatik Hareket Akışı vardır.
- Oluşturma, koordinatöre yönlendirme, saha ataması, kabul, yola çıkma, müdahale ve tamamlanma hareketleri sistem tarafından otomatik yazılır.
- Sistem Yönetimi menüsündeki Geri Bildirimler adı Hareket Akışı olarak değiştirildi.
- İşlem Logları teknik denetim kaydı olarak ayrıca korunur.


V6 FINAL
- Sistem haritasında her talep ayrı konum pini olarak gösterilir.
- Eski haritasız talepler backfill_talep_konumlari komutuyla otomatik konumlandırılır.
- Yeni talepler adres üzerinden backend'de otomatik konumlandırılır.
- Harita durum renkleri: Bekleyen kırmızı, İşlemde turuncu, Tamamlandı yeşil.
- Aciliyet renkleri bu durum paletinden ayrıdır:
  Düşük mavi, Normal gri, Yüksek mor, Acil fuşya/bordo.
- Kullanıcılar ekranında yalnız bir "Kayıt Ekle" gridi vardır.
- Kayıt Alanı seçimiyle Otomatik Organizasyon veya tek rol/personel kaydı seçilir.
- Otomatik Organizasyon: eksik ilçe koordinatörleri + eksik uzman saha ekipleri.
- 185 talebi başarılı kaydedilince form üç aşamalı reset korumasıyla tamamen temizlenir.


V7 OPERASYON FINAL
- Saha durumu kontrollü state-machine akışına alındı:
  Sahaya Atandı -> Kabul Etti -> Yola Çıktı -> Adrese Ulaştı ->
  Müdahale Ediliyor -> Tamamlandı.
- Saha personeli yalnız sıradaki doğru işlem butonunu görür; aşama atlayamaz.
- Durum değiştiren endpointler POST çalışır; yanlışlıkla link açılması durum değiştirmez.
- Her saha butonu otomatik GeriBildirim + IslemLogu üretir.
- Saha Notu, manuel geri bildirim değildir. Operasyonel açıklama olarak yazılır;
  sistem bunu otomatik hareket kaydına ve loga dönüştürür.
- Koordinatör ekranında "Canlı Saha Operasyonları" vardır.
- Koordinatör saha durumunu değiştirmez; ekiplerin ilerleyişini izler.
- Koordinatör ekranı 8 saniyede bir merkezi API'den durum günceller.
- 185 talep gridindeki saha durumları da 8 saniyede bir güncellenir.


V8 YÖNETİM FINAL
- Sistem Yöneticisi artık operasyonel rol değildir:
  yeni talep oluşturamaz, koordinatör adına sahaya atama yapamaz,
  saha adına durum ilerletemez veya saha notu yazamaz.
- 185 Personeli talep oluşturur.
- Koordinatör yalnız kendi sorumluluğundaki bekleyen talebi sahaya atar.
- Aynı saha hesabına aynı anda ikinci aktif operasyon atanmaz.
- Aktif talep sorumluluğu olan personel pasife alınamaz.
- Müsaitlik ve kullanıcı aktif/pasif işlemleri POST ile yapılır.
- Sistem dashboard'ında 12 ilçe için şef/koordinatör ve saha kapasite gridi vardır.
- Yeni "Personel & Saha" ekranında:
  Sistem yöneticileri,
  185 personelleri,
  tüm ilçelerin şef/koordinatörleri,
  iletişim/rol/uzmanlık bilgileri,
  saha ekipleri,
  görev/müsaitlik bilgileri birlikte listelenir.
- Teknik işlem logu operasyonel kullanıcıların her ekranını kaplamaz;
  Sistem Yöneticisi için denetim amaçlı tutulur.


V9 ŞEF ONAY FINAL
- Saha personelinin "İşi Bitirdim" işlemi artık talebi doğrudan Tamamlandı yapmaz.
- Saha personeli zorunlu "Şefe Sonuç Notu" yazar:
  arızanın nedeni, yapılan işlem ve kontrol sonucu.
- Talep "Şef Onayı Bekliyor" durumuna geçer.
- 185, sistem yönetimi, harita ve koordinatör ekranlarında bu kayıt tamamlanmış sayılmaz.
- Koordinatör/şef ekranında "Onay Bekleyen İşler" bölümü vardır.
- Şef:
  1) Onayla ve Tamamla
  2) Gerekçeyle Sahaya Geri Gönder
  işlemlerinden birini seçer.
- Yalnız şef onayından sonra durum "Tamamlandı" olur.
- Log ve Otomatik Hareket Akışı sistem tarafından korunur; onay işlemi log sayfasından yapılmaz.
- Her saha bitiş bildirimi, şef onayı ve şef iadesi otomatik hareket + teknik log üretir.
- Koordinat 6 ondalık hassasiyet düzeltmesi V9 içine dahil edilmiştir.


V10 SAHA HESABI / AYNI TALEP İADESİ
- Koordinatör saha atama ekranında her ekibin gerçek giriş kullanıcı adı görünür.
- Atama seçiminde kullanıcı adı da gösterilir (örn. @kanal_golcuk).
- Canlı Saha Operasyonları kartında "Saha hesabı: @..." bilgisi ve kopyalama butonu vardır.
- Talep detayında atanan saha giriş hesabı görüntülenir.
- Şef "Sahaya Geri Gönder" yaptığında YENİ TALEP OLUŞMAZ.
- Aynı ISU-2026-XXXXXX talep/arıza numarası korunur.
- İade aynı saha ekibine mevcut kayıt üzerinden geri döner.
- İade gerekçesi hareket akışı ve teknik logda saklanır.
- Önceki saha sonuç notu hareket geçmişinde korunur; yeni müdahale turu için sonuç notu alanı temizlenir.


V11 GLOBAL ŞEF ONAY DURUMU
- "Şef Onayı Bekliyor" artık bağımsız bir durum olarak bütün ekranlarda aynı görünür.
- 185 ekranında ayrı "Şef Onayı" sayacı vardır.
- Sistem Yönetim Panelinde ayrı "Şef Onayı" kartı vardır.
- Haritada Şef Onayı bekleyen talep ayrı durum rengiyle gösterilir.
- Talepler gridinde durum etiketi "Şef Onayı Bekliyor" olarak görünür.
- Saha bitirdiği işi şef onayı olmadan "Tamamlandı" sayamaz.
- V9/V10 akışından geçmiş, saha bitiş zamanı bulunan fakat şef onayı bulunmayan
  yanlışlıkla Tamamlandı durumundaki kayıtlar migration ile otomatik olarak
  "Şef Onayı Bekliyor" durumuna düzeltilir.


V12 VATANDAŞ BİLGİLENDİRME / KAPANIŞ
- Teknik operasyon durumu ile vatandaş geri dönüş durumu ayrıldı.
- Şef "Onayla ve Tamamla" dediğinde:
  1) Talep teknik olarak Tamamlandı olur.
  2) Otomatik olarak 185 "Vatandaş Bilgilendirme" kuyruğuna düşer.
- 185 ekranında üçüncü sekme:
  Yeni Talep | Talepler | Vatandaş Bilgilendirme
- Kuyruk kartında:
  Talep no, vatandaş ad-soyad, telefon, e-posta, tam adres,
  iş türü/alt türü, arıza açıklaması, saha sonuç notu,
  saha ekibi ve şef onay zamanı görünür.
- Telefon "Ara" ve "Numarayı Kopyala" işlemleri vardır.
- Kontrollü sonuçlar:
  Vatandaş Bilgilendirildi / Ulaşılamadı / Tekrar Aranacak.
- Ulaşılamadı ve Tekrar Aranacak kayıtları kuyrukta kalır.
- Bilgilendirildi seçildiğinde vatandaş geri dönüş işi kapanır.
- Her arama sonucu VatandasAramaKaydi tablosunda tarih/kullanıcı/sonuç ile tutulur.
- Her işlem otomatik Hareket Akışı + teknik Log üretir.
- Manuel geri bildirim kutusu geri getirilmemiştir.
- 185 yeni talep formunu doldururken başka tarayıcıdan şef onayı gelirse
  sayfa otomatik yenilenmez; form bozulmadan canlı bildirim/badge gösterilir.
- Sistem Yönetimi talepler tablosunda vatandaş geri dönüş durumu ayrıca görünür.


V12.1 SABİT AÇIK VATANDAŞ BİLGİLENDİRME GRID
- Vatandaş Bilgilendirme artık açılır/kapanır bir panel veya sekme değildir.
- 185 ekranında sürekli açık ayrı bir çalışma alanıdır.
- Şefin onayladığı teknik olarak tamamlanan işler otomatik olarak bu gridin en üstüne düşer.
- 185 personeli:
  vatandaş bilgilerini, telefonu, adresi, arıza türünü, saha sonuç notunu ve şef onayını
  aynı kartta görür.
- Vatandaş Bilgilendirildi denilen kayıt aktif kuyruktan çıkar,
  aynı ekranın altındaki "Bilgilendirilen / Kapanan İşler" gridine otomatik taşınır.
- Ulaşılamadı / Tekrar Aranacak kayıtları aktif gridde kalır.
- Kapananlar bölümü de sürekli açık ve görünürdür.


V13 SOL ARAMA KUYRUGU + DETAY KONSOLU
- Vatandas bilgilendirme alani sade bir iki kolonlu operasyon konsoluna donusturuldu.
- Sol tarafta dikkat cekici, kaydirilabilir 185 arama kuyrugu bulunur.
- Kuyruk satirinda yalniz kisa bilgiler: sira, talep no, ariza, vatandas, telefon ve tamamlanma/onay saati.
- Kuyruk kaydina tiklandiginda sayfa degismeden sag tarafta tum detaylar acilir.
- Sag detayda: vatandas, ariza, adres, koordinat, mini harita, saha sonucu, sef onayi, arama gecmisi ve sistem hareketleri vardir.
- Operasyon zaman cizelgesi: talep gelisi, koordinatore yonlendirme, saha atamasi, saha bitisi, sef onayi ve 185 aramasi.
- Yeni Talep formu da sadeleştirildi: solda Konum & Harita, ortada Ariza Detayi, sagda Vatandas Bilgileri.
- Veri modeli ve V12 vatandas bilgilendirme akisi degismedi; yeni migration gerekmez.


V14 ÜST DÜZEY 185 ARAYÜZÜ
- V13'te görülen stil/cache problemi için benzersiz cagri185_v14.css ve cagri185_v14.js kullanılır.
- Vatandaş geri dönüş merkezi master-detail çağrı konsolu olarak yeniden tasarlandı.
- Sol sütun: sabit, koyu ve kaydırılabilir arama kuyruğu.
- Kuyrukta yalnız sıra, talep no, arıza, vatandaş, telefon ve tamamlanma/onay saati bulunur.
- Tıklanan kayıt sağ panelde açılır.
- Sağ panel: operasyon zaman çizelgesi, vatandaş, arıza, adres+harita, saha sonucu, personel/onay ve tüm hareket geçmişi.
- 185 görüşme işlemleri ayrı ve dikkat çekici işlem kartında tutulur.
- Kapanan işler arşivi ana ekranı kalabalıklaştırmaması için aşağıda açılır bölüm olarak tutulur.


V15 RAPOR + ARAMA KANIT AKIŞI
- Sistem Raporları: tarih, ilçe, mahalle, cadde/sokak, iş türü ve durum filtreleri.
- Harita ölçeği: ilçe / mahalle / cadde-sokak. Daire büyüklüğü arıza sayısını gösterir.
- İlçe, mahalle ve cadde bazlı yoğunluk tabloları + filtrelenmiş İş Listesi.
- CSV indirme artık seçili rapor filtrelerine uyar.
- 185 vatandaş araması iki aşamalı: Aramayı Başlat -> Görüşme Sonucu.
- Arama başlangıcı IslemLogu'na kullanıcı, IP ve saat ile kaydolur.
- Sonuç, açık arama oturumu olmadan kaydedilemez; aynı kayıt iki operatör tarafından eşzamanlı aranamaz.
- Sonuç logunda başlangıç, sonuç saati ve uygulama oturum süresi bulunur.
- Bu denetim uygulama içi kanıttır. Gerçek hat bağlantısı/konuşma için PBX/CTI entegrasyonu gerekir.


V16 OTOMATİK OPERASYON RAPORU
- Rapor sayfasındaki manuel tarih/ilçe/mahalle/cadde/durum filtre formu kaldırıldı.
- Rapor verileri tamamen Talep ve IslemLogu kayıtlarından otomatik hesaplanır.
- Yeni talep, saha atama/durum değişimi, şef onayı veya 185 vatandaş kapanışı olduğunda
  rapor sürümü değişir ve açık rapor ekranı 5 saniye içinde otomatik yenilenir.
- Harita V15'teki yoğunluk balonları yerine Sistem Yönetim Dashboard'undaki
  önceki tek-talep pin yapısına döndürüldü.
- Haritada her talep ayrı pindir:
  pin ana rengi = operasyon durumu,
  pin çekirdeği = aciliyet.
- İlçe, mahalle ve cadde/sokak yoğunluğu otomatik hesaplanır ve en yoğun bölgeler sıralanır.
- Manuel veri girişi yoktur.
- Güncel İş Listesi raporun altında otomatik oluşur.
- CSV çıktısı tüm güncel iş kayıtlarından otomatik oluşturulur.
- Yeni migration yoktur; mevcut veriler korunur.


V17 SADE 185 GERİ BİLDİRİM FORMU
- V15'teki "Aramayı Başlat / uygulama oturumu / sayaç" yapısı kullanıcı arayüzünden kaldırıldı.
- 185 personeli vatandaşı kurum telefonundan arar ve görüşme bittikten sonra sonucu sisteme girer.
- Tek ve sade form:
  1) Görüşme Sonucu: Görüşüldü / Ulaşılamadı / Tekrar Aranacak
  2) Görüşüldü ise Vatandaş Memnuniyeti: İyi / Normal / Kötü
  3) İşlem Süresi (dakika)
  4) Opsiyonel kısa görüşme notu
- Görüşüldü kaydında memnuniyet ve işlem süresi zorunludur.
- Tek "Geri Bildirimi Kaydet" butonu kullanılır.
- Ulaşılamadı / Tekrar Aranacak kayıtları kuyrukta kalır.
- Görüşüldü kaydı vatandaş geri bildirim sürecini kapatır.
- Sonuç; kullanıcı, talep, tarih/saat, memnuniyet, işlem süresi ve not ile
  Hareket Akışı + Sistem Loguna otomatik kaydedilir.
- Veritabanı şeması değiştirilmedi; yeni migration yoktur.


V18 MÜŞTERİ/VATANDAŞ MEMNUNİYETİ
- Genel Memnuniyet: İyi / Normal / Kötü
- Sorun Çözüldü mü: Evet / Kısmen / Hayır
- Hizmet Hızı: Hızlı / Normal / Yavaş
- Bilgilendirme Yeterli miydi: Yeterli / Kısmen / Yetersiz
- İşlem Süresi ve opsiyonel kısa görüşme notu
- Görüşüldü durumunda bu değerlendirmeler zorunludur.
- Ulaşılamadı / Tekrar Aranacak durumunda değerlendirme alanları gizlenir.
- Sonuçlar hareket akışı ve sistem loguna otomatik yazılır.
- Yeni migration yoktur.


V19 GENİŞ GERİ BİLDİRİM + OPSİYONEL ANKET
- Sağ kenardaki küçük geri bildirim kutusu kaldırıldı; bölüm sayfanın altını tam genişlikte kaplar.
- Önceki arama/kapanış kayıtları yatay kaydırılabilir şerit olarak gösterilir.
- Temel kapanış kaydı: Görüşme Sonucu + Genel Memnuniyet + İşlem Süresi + opsiyonel Görüşme Notu.
- Altında ayrı "Vatandaş Memnuniyet Anketi" bulunur. Anket tamamen OPSİYONELDİR.
- Anket soruları: sorun çözümü, hizmet hızı, bilgilendirme, personel iletişimi ve 1-5 genel hizmet puanı.
- Anket boş bırakılarak geri bildirim kaydedilebilir.
- Yeni migration yoktur; mevcut veriler korunur.


V20 MEMNUNİYET ANALİZİ
- Sistem Yönetim Paneli sol menüsüne “Memnuniyet Analizi” eklendi.
- 185 görüşme sonrası memnuniyet ve opsiyonel anket kayıtları analiz ekranında listelenir.
- Özet göstergeler: tamamlanan görüşme, ankete katılan, katılım oranı, ortalama puan, olumlu memnuniyet, dikkat gerektiren kayıt.
- Talep no / vatandaş / 185 personeli araması ve ilçe filtresi vardır.
- Düşük veya olumsuz değerlendirmeler tabloda dikkat satırı olarak vurgulanır.
- Mevcut VatandasAramaKaydi kayıtları kullanılır; yeni migration yoktur.

V21 KOMPAKT GERİ DÖNÜŞ
- 185 geri dönüş alanı ince satırlı ve yatay kaydırılabilir tabloya dönüştürüldü.
- Vatandaş adının yanındaki i butonu ayrıntıları popup açar.
- Koordinata tıklanınca popup içinde küçük harita açılır.
- Geri bildirim formu popup içinde açılır; anket opsiyonel ve katlanabilirdir.
- V20 Memnuniyet Analizi aynen korunur.
- Yeni migration yoktur.


V22 — ARAMA AKSİYONLARI VE KOMPAKT KAPANAN İŞLER
- Canlı Arama Kuyruğu satırlarına Ara, Kopyala ve Arandı butonları eklendi.
- Ara: tel: bağlantısını açar.
- Kopyala: telefon numarasını panoya kopyalar.
- Arandı: geri bildirim/sonuç popup'ını açar ve Görüşüldü seçeneğini hazırlar.
- Görüşüldü kaydedilirse kayıt kuyruktan otomatik çıkar ve Kapanan İşler'e geçer.
- Ulaşılamadı veya Tekrar Aranacak kaydedilirse kayıt kuyrukta kalır.
- Kapanan İşler paneli ince satırlı, yatay kaydırılabilir ve her açılışta kapalıdır.
- Yeni migration yoktur; mevcut veriler korunur.

V23 — RAPOR MERKEZİ + OTOMATİK KISA ANKET
- Sistem Yöneticisi sol menüsüne Rapor Merkezi eklendi.
- Tarih aralığını yönetici belirler; varsayılan dönem içinde bulunulan aydır.
- Hızlı dönemler: Bugün / Son 7 Gün / Bu Ay.
- Detaylı rapor ekranı sağa-sola kaydırılabilir.
- Talep no, vatandaş, telefon, e-posta, adres, koordinat, iş türü/alt türü,
  şef/koordinatör, saha, zamanlar, şef onayı, tekrar başlatma/iade,
  vatandaş geri dönüşü ve anket sonuçları raporlanır.
- Dışa aktarım: Excel (.xlsx), PDF, CSV ve JSON.
- PDF ayrıntıları okunabilir kayıt kartları şeklinde üretir.
- 185 Arandı popup'ında 4 soruluk opsiyonel anket otomatik görünür.
- i bilgi popup'ında Arama & Anketi Aç kısayolu bulunur.
- Anket zorunlu değildir.
- Yeni migration yoktur; mevcut veriler korunur.

V24 — YATAY DETAYLI RAPOR
- PDF raporu artık talep başına ayrı form/kart şeklinde oluşturulmaz.
- Tüm talepler tek geniş tabloda satır satır listelenir.
- PDF sayfası özellikle geniş hazırlanır; PDF görüntüleyicide sağa/sola kaydırılarak incelenir.
- Başlık satırı her dikey sayfada tekrar eder.
- Excel, CSV ve JSON dışa aktarımları aynı detaylı veri yapısını korur.
- Web Rapor Merkezi sağa/sola kaydırılabilir geniş tablo olarak kalır.
- Yeni migration yoktur.

V25 — SADE / KOMPAKT 185 + YATAY RAPOR
- Kullanıcı arayüzündeki gereksiz teknik durum etiketleri kaldırıldı.
- 185 Aranacak Vatandaşlar kuyruğu sayfanın üst bölümüne taşındı.
- Yeni Talep ekranı daha kısa ve dengeli hale getirildi.
- Adres formu ile harita aynı kart içinde yan yana yerleştirildi.
- Arıza ve vatandaş kartları sağ kolonda boşluk bırakmadan üst üste yerleştirildi.
- Kapanan İşler kompakt ve varsayılan kapalı kalır.
- Rapor Merkezi tablo alanı sabit yükseklikte; hem sağa/sola hem gerektiğinde yukarı/aşağı kendi içinde kayar.
- Her talep raporda tek satırdır.
- İlk iki rapor kolonu yatay kaydırmada sabit kalır.
- PDF her talebi tek yatay satırda gösteren çok geniş sütun tablosu üretir.
- Excel / CSV / JSON ayrıntılı alanları korur.
- Yeni migration yoktur.

V26 — 185 DENGELİ İKİ KOLONLU GRID
- Yeni Talep ekranında en üstte Vatandaş Bilgileri ve Talep & Arıza Bilgisi yan yana gösterilir.
- Sol kolon: Vatandaş Bilgileri, hemen altında Konum & Harita.
- Sağ kolon: İş Türü, İş Alt Türü, Öncelik ve Arıza Açıklaması.
- Sol ve sağ ana kolonlar eşit genişlikte ve dengeli yükseklikte düzenlendi.
- Harita küçültüldü ve konum alanıyla aynı kompakt kart içinde gösterildi.
- Aranacak Vatandaşlar bölümü yeni talep formunun hemen altına alındı.
- Aranacak Vatandaşlar grid'i belirgin yeşil tonlarla vurgulandı.
- Kapanan İşler açılır/kapanır kompakt yapısını korur.
- Rapor Merkezi ve diğer V25 özellikleri aynen korunur.
- Yeni migration yoktur.

V27 — ÖNCELİK BAZLI SAHAYA ATAMA SLA
- İç operasyon için öncelik bazlı sahaya atama hedefleri eklendi:
  Acil: 30 dakika
  Yüksek: 60 dakika
  Normal: 120 dakika
  Düşük: 240 dakika
- Süre, talebin şef/koordinatör kuyruğuna düştüğü anda başlar.
- Sürenin %75'i kullanıldığında "SLA Yaklaşıyor" uyarısı görünür.
- Hedef süre aşılırsa "SLA AŞILDI" ve gecikme dakikası gösterilir.
- Şef / Koordinatör panelinde atama bekleyen kayıtlar en az kalan süreye göre sıralanır.
- Sistem Yönetim Panelinde geciken ve süresi yaklaşan talepler ayrı SLA panelinde görünür.
- Sistem > Tüm Talepler listesine SLA sütunu eklendi.
- Detaylı Rapor Merkezi'ne SLA hedefi, gerçek atama süresi ve SLA sonucu eklendi.
- Bu süreler resmi kurum SLA'sı olarak değil, proje içi operasyon hedefi olarak tanımlanmıştır.
- Yeni migration yoktur.


V28 — KURUMSAL ENTEGRE SÜRÜM
============================

1) GENEL İCMAL + DETAYLI RAPOR
- Rapor Merkezi artık iki katmanlıdır:
  • Genel İcmal: toplam talep, toplam/açık/tamamlanan iş emri, şef onayı, ortalama bitiş.
  • Birim İcmali: İş emri gönderen birim, toplam, açık, tamamlanan, ortalama bitiş.
  • Detaylı Rapor: mevcut geniş yatay talep tablosu korunur.
- Detaylı rapora İş Emri No, Gönderen Birim ve Abone No eklendi.
- Excel çıktısında Genel İcmal + Detaylı Rapor birlikte bulunur.

2) ABONE / ABONELİK
- Yeni Abone modeli: Abone No, Sayaç No, ad-soyad, telefon, e-posta ve adres.
- Sistem Yönetimi > Aboneler sayfası eklendi.
- 185 Yeni Talep ekranında Abone No + Abone Sorgula eklendi.
- Bulunan abone vatandaş bilgilerine bağlanır; talep abone kaydıyla ilişkilendirilir.
- Abonelik zorunlu değildir; abone olmayan vatandaş için normal talep akışı devam eder.

3) İŞ EMRİ
- Talep ile İş Emri ayrıldı.
- Şef sahaya atama yaptığında otomatik IE-YYYY-XXXXXX numaralı İş Emri oluşur.
- Gönderen Birim, saha ekibi, durum ve operasyon zamanları İş Emrinde tutulur.
- Sistem Yönetimi > İş Emirleri ekranı eklendi.
- İş emri detay formu yazdırılabilir / PDF olarak kaydedilebilir.
- Saha hareketleri ve şef onayı iş emrini otomatik günceller.

4) ANDROID / MOBİL SAHA
- /mobil/saha/ adresinde Android telefon için özel saha ekranı eklendi.
- Saha personeli İş Emrini Kabul → Yola Çık → Adrese Ulaş → Müdahale → Şef Onayına Gönder adımlarını telefondan ilerletebilir.
- MOBIL_BASLAT.bat aynı Wi-Fi ağındaki telefondan erişim için sunucuyu 0.0.0.0:8000 üzerinde açar.
- JSON mobil API:
  POST /api/mobil/giris/
  GET  /api/mobil/is-emirleri/
  POST /api/mobil/is-emri/<id>/durum/
- android_saha_app klasöründe Android Studio kaynak projesi vardır.
- Android APK oluşturmak için Android Studio / Android SDK gerekir.

VERİTABANI
- 0005_abone_isemri_mobil migrationı vardır.
- Güncellemeden önce db.sqlite3 yedeği alınmalıdır.
- migrate çalıştırılması zorunludur.
