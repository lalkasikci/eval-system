# İki Uzmanla Kör Değerlendirme Protokolü

**Aşama 4 + 9 insan doğrulama bileşeni.** Şu anda hiç kimsenin değerlendirmesi yapılmış gibi gösterilmiyor.

1. Senaryolardaki ölçüm ve ekonomi yorumlarını reklam/performans uzmanı A ve ürün/KOBİ deneyimi uzmanı B bağımsız olarak okusun. Her ikisi de v1 beklenen kararları görmeden önce kendi kararını kaydetsin.
2. `allowed_decisions`, `must_include` ve `must_not_include` için anlaşmazlıkları yazın. Gerekçeli çözüm olmadan “approved” yazmayın. Gerekli değişiklikleri veri kümesinde sürüm yükselterek uygulayın, geçmiş koşuları silmeyin.
3. Çıktı metinleri için `python -m madset_eval review-export <run-json> --out ...` komutunu kullanın. Hazır kör paket `outputs/expert_review_BLIND_V2.csv` dosyasındadır. İki uzman farklı satırda `correct_decision`, 7 adet `0–4` boyut puanı, F-kodları ve `overall_pass` alanlarını doldursun.
4. Her öneriyi A/B sürüm adı, otomatik skor ve üretilen kod bilgisi gizlenmiş halde puanlayın. Uygun olan yerde N/A'ları gerekçeli kullanın; biçim belirsizliğinde not düşülmeli.
5. İki uzman tamamlayınca `python -m madset_eval review-analyze <csv>` ile ikili geçiş uyumunu, Cohen kappa'yı ve otomatik grader'ın uzman konsensüsüne göre recall/yanlış-alarm oranını ölçün. Uyuşmazlıkları üçüncü değerlendirme/uzlaşma ile kapatın.
6. Model tabanlı grader eklenirse aynı kör kümede ayrıca kalibre edilmeli.
7. Uzmanlardan gelen bir vaka kodunu/promptu geliştiriyorsa o vaka artık kör test değildir; yeni bir holdout oluşturun.

## Kesin yayın şartı

Bu belgedeki inceleme yapılmadan v3 demo %100 verse bile **üretim için güvenli** anlamına gelmez. İş gereksinimlerine göre geçiş eşikleri ve önemli hata ağırlıkları yeniden belirlenmelidir.
