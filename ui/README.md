# MADSET — Öneri Aksiyonları Arayüzü (v1.0)

Bu arayüz **frontend demodur**. Meta/Google API anahtarı, müşteri hesabı veya üretim veritabanına bağlanmaz. Gerçek bütçe, pause veya restart değişikliği **yapmaz**. Bütün örnek markalar, durumlar ve nesne kimlikleri sentetiktir.

## Aç

`index.html` dosyasını tarayıcıda çift tıkla aç. İnternet, Node.js veya API anahtarı gerekmez. Mobil ve masaüstü uyumludur.

## Ekranlar

- **Öneriler:** 14 örnek kart, 4 etkileşim türü, filtreleme ve arama.
- **Aksiyon Kütüphanesi:** Kullanıcının verdiği 25 finding → aksiyon haritasının eksiksiz listesi; Pause/Restart henüz hiçbir finding tarafından tetiklenmiyor.
- **Eval Sonuçları:** Önceki laboratuvarın *yerel demo* V1/V2/V3 özeti; başka bir `SUMMARY.json` dosyası dosya seçiciyle yüklenebilir.

## Etkileşimler

- **Bütçeyi %10 artır:** Gerçek bütçeyi değiştirmeden önce onay modalı açar. Demo onayı yalnızca arayüzde simüle edilmiş değer üretir; bütçe sahibi nesne (campaign/adset) belirtilir. Gate kapalıysa sırasıyla `winner_underfunded → /control-panel`, `scaling_ready → /publish` fallback'i sunulur.
- **Duraklat/Yeniden başlat:** Şu an hiçbir finding kullanmayan operasyon örnekleri. Üç nesnenin durumunu **simüle** eder; backend doğrulaması değildir.
- **Yönlendirme:** Rota görüntüler; Madset uygulaması temel adresi kullanıcı tarafından ayarlanmadıysa gerçek navigasyon denemez. `<grup>` ve `<kreatif>` için örnek, sentetik değerler kullanılır.
- **Takip:** Bir sonraki kontrol tarihini seçip kartı takipte işaretler. Tarayıcının localStorage alanında saklanır; sunucuya veya görevlere gitmez.
- **Bilgi kartı:** Hiç aksiyon düğmesi yoktur.

## Gerçek backend entegrasyonu için

`action_catalog.json` otoriter finding → aksiyon haritasıdır. `BACKEND_CONTRACT.md` gerçek Meta işlemleri ve readback gerekliliklerini tanımlar. Bu prototip gerçek Meta hesabına **bağlı değildir** ve işlemlerin tamamlandığını iddia etmez.
