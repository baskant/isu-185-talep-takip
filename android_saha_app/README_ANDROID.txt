İSU 185 ANDROID SAHA UYGULAMASI — V31

Bu Android Studio projesi V31 Mobil Saha ekranını açar ve:
- kamera/file input desteği,
- GPS/konum izni,
- yeni iş emri / şef geri gönderme için yerel Android bildirim kontrolü,
- aynı Django oturumu ve aynı veritabanı
ile çalışacak şekilde güncellenmiştir.

Yerel test:
1) PC ve Android telefon aynı Wi-Fi ağına bağlanır.
2) Ana projede MOBIL_BASLAT.bat çalıştırılır.
3) PC IPv4 adresi alınır (örn. 192.168.1.25).
4) Android uygulamanın ilk açılışında 192.168.1.25:8000 girilir.
5) Saha hesabıyla giriş yapılır.
6) Kamera, konum ve bildirim izinleri verilir.

Mobil saha:
- İş emrini kabul et
- Yola çık
- GPS ile adrese ulaş
- Müdahale öncesi fotoğraf çek
- Müdahaleye başla
- Müdahale sonrası fotoğraf + sonuç notu
- Şef onayına gönder

Not:
Uygulama sunucudaki bildirim API'sini çalışırken periyodik kontrol ederek Android
yerel bildirimi üretir. Uygulama tamamen kapatılmış/işletim sistemi tarafından
öldürülmüşken garantili push için üretim ortamında Firebase Cloud Messaging (FCM)
gibi bir push servisi ve kurum sunucu anahtarları gerekir.
