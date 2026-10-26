# MADSET — Üç Ölçülmüş İterasyon

## Metrik kayıtları - legacy grader 1.0

Bu kayıtlar **üç yerel kural tabanlı örnek üreticiye** aittir; canlı Madset modelinde ölçüm yapılmamıştır. Aynı 40 sentetik vaka, her sürümde 3 kez çalıştırılmıştır.

| Sürüm | Fark | Dev geçiş (30 vaka × 3 deneme) | Holdout geçiş (10 vaka × 3 deneme) |
|---|---|---:|---:|
| v1 | Sadece tıklama hacmiyle kaba karar; kasıtlı zayıf referans | 0/90 (%0.0) | 3/30 (%10.0) |
| v2 | Ölçüm bozukluğu, yeni kampanya ve hedef sonuç maliyeti ayrımı | 57/90 (%63.3) | 9/30 (%30.0) |
| v3 | Sektörel kapasite, huniler, gerçek sıfır, dönem normalizasyonu ve kontrollü test | 90/90 (%100.0) | 30/30 (%100.0) |

Grader 1.1'in semantik kapısı aynı eski set yeniden çalıştırıldığında V1/V2/V3 dev geçişlerini sırasıyla %0 / %16,7 / %100; ilk holdout geçişlerini %0 / %0 / %80 ölçtü. Legacy rakamlar tarihsel iterasyon kaydı olarak korunur; güncel kabul kararında grader 1.1 kullanılır.

## Regresyonlar / iyileşmeler
- dev: v1→v3, +100.0 yüzde puan; iyileşenler: ADV-001, ADV-002, ADV-003, ADV-004, ADV-006, ADV-007, ADV-008, ADV-009, ADV-011, ADV-012, ADV-013, ADV-014, ADV-015, ADV-017, ADV-018, ADV-019, ADV-020, ADV-022, ADV-023, ADV-024, ADV-025, ADV-026, ADV-028, ADV-029, ADV-031, ADV-033, ADV-035, ADV-036, ADV-038, ADV-039; gerilemeler: —.
- holdout: v1→v3, +90.0 yüzde puan; iyileşenler: ADV-010, ADV-016, ADV-021, ADV-027, ADV-030, ADV-032, ADV-034, ADV-037, ADV-040; gerilemeler: —.

## Grader öz-test sonuçları
- Negatif mutasyon: 8, hedef hata yakalama: %100.
- Pozitif kontrol: 19, yanlış alarm: %0.
- **Sınırlama:** Bunlar algoritmanın kapsadığı örneklerdir; stratejik öneri doğruluğunun ve Türkçe anlam denetiminin doğrulanması değildir. %100 sonucu küçük/kurgusal veri kümesinde doygunluk/heuristik rubric zayıflığına işaret eder.

## Tespit edilen grader regresyonu ve düzeltme
- İlk testte “garanti değildir” ifadesi yanlışlıkla F03 ile reddedildi. Olumsuz bağlam kontrolü eklendi; özellikle ACT ve ihtiyatlı önerileri içeren pozitif kontrol kümesi genişletildi. Bu düzeltme **geliştirme vakalarındaki** yanlış alarm üzerinden yapıldı.
- Demo sırasında holdout sonuçları incelendiğinden bu sabit 10 vaka **ileriye dönük bağımsız değerlendirme için tüketilmiştir**. Yeni sürüm/model kabulü için yeni gizli holdout oluşturulmalıdır.

## Yeni kör doğrulama — holdout_v2

V3/refactor tamamlandıktan sonra 12 yeni vaka ve gold beklentisi SHA-256 ile donduruldu; bundan sonra üretici değiştirilmeden V1/V2/V3 üçer trial çalıştırıldı.

| Sürüm | İlk kör geçiş | Grader 1.1 ile aynı transcript |
|---|---:|---:|
| v1 | 0/36 (%0) | 0/36 (%0) |
| v2 | 0/36 (%0) | 0/36 (%0) |
| v3 | 24/36 (%66,7) | 27/36 (%75) |

İlk V3 koşusunda ADV-041, ADV-044, ADV-049 ve ADV-050 başarısız oldu. ADV-050, olumsuz yönergedeki “garanti ... kullanmayın” ifadesinin yanlış F03 alarmıydı; grader düzeltildi ve aynı kayıt yeniden puanlandı. Kalan üç başarısızlık üreticiye aittir: gecikmeli randevu bağlamı, kârlı görünse de korunması gereken kampanya kararı ve iptal bilgisinin ölçüm arızası sanılması. Kör sonuç görüldükten sonra V3 değiştirilmedi.

## Karar ve bakım
- Bu paket bir demo ve teknik eval iskeleti olarak kabul edilebilir.
- Gerçek Madset modeli, iki uzman onayı ve genişletilmiş gerçek-kalite grader uyumu olmadan “ürüne hazır” kabul edilmez.
- Yeni hatalar yeni senaryoya ve uygun regresyon testine dönüşür; eski sonuç kayıtları silinmez.

## Claude LLM yargıç doğrulaması

Kayıtlı V3 geliştirme çıktılarının 30 benzersiz senaryosu Claude Sonnet 4.6 ile değerlendirildi. Sonuç 25/30 geçiş (%83,33), 30/30 doğru karar, 91,04 ortalama puan ve sıfır kritik hata oldu. ADV-001, ADV-003, ADV-014, ADV-017 ve ADV-038 geçemedi. Claude'un ortak eleştirisi; mevcut satış/huni/ekonomi verilerinin eksik kullanılması ve önerilerin somut zaman, eşik ve kontrol planı vermemesiydi.

Koşu 57.952 girdi ve 20.395 çıktı tokenı kullandı; ortalama yargıç gecikmesi 13,89 saniyeydi. Fiyatlar sabitlenmediği için maliyet kaydı `null` kaldı. ADV-001'in tek-vaka kontrolde 92,5, toplu koşuda 76,25 alması LLM yargıç değişkenliğini gösterdi. Bu kayıt bir iterasyon ölçümüdür; insan kalibrasyonu veya ürün yayın onayı değildir.
