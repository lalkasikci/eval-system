# MADSET — Advise Lab Değerlendirme Raporu

## 1. Yönetici özeti
Bu rapor **canlı Madset ürününü değil**, 40 sentetik girdide çalıştırılan üç yerel kural tabanlı demo üreticisini (v1/v2/v3) ölçer.
Öneri motoruna platform API erişimi verilmedi, reklam üzerinde işlem yapılmadı ve gerçek müşteri verisi kullanılmadı.
Bu çalıştırma **ürün kalitesi kanıtı** değildir; uçtan uca değerlendirme altyapısının teknik gösterimidir.

## 2. Veri kümesi ve yöntem
- Geliştirme: 30 senaryo; bağımsız holdout: 10 senaryo (%25).
- Her vakada beklenen karar kümesi üretimden **önce** dosyaya yazıldı.
- Holdout beklentileri üreticiye verilmedi; yalnız puanlama aşamasında açıldı.
- Rubric: yedi ağırlıklı boyut (toplam 100); geçme: en az 80, kabul edilen karar, sıfır doğrulanmış kritik hata.
- Çıktı JSON sözleşmesi ve aritmetik kontroller deterministik; açık uçlu nitelik puanlaması **heuristic**, uzman onayı gerekir.

## 3. Üç sürümün gerçek çalıştırma sonuçları
| Set | Sürüm | Geçti | Karar doğruluğu | Kritik hata oranı | Ortalama skor |
|---|---|---:|---:|---:|---:|
| dev | v1 | 0/90 (0.0%) | 13.3% | 76.7% | 46.08 |
| dev | v2 | 15/90 (16.7%) | 63.3% | 0.0% | 71.00 |
| dev | v3 | 90/90 (100.0%) | 100.0% | 0.0% | 100.00 |
| holdout | v1 | 0/30 (0.0%) | 10.0% | 60.0% | 46.88 |
| holdout | v2 | 0/30 (0.0%) | 30.0% | 0.0% | 62.38 |
| holdout | v3 | 24/30 (80.0%) | 90.0% | 0.0% | 94.38 |

Birinci sürümde tıklama ağırlıklı acele aksiyonlar, ikinci sürümde zaman/ölçüm kontrolleri, üçüncü sürümde bağlam ve dönüşüm hunisi kontrolleri eklendi. Bu sürümler demo algoritmalarıdır.

## 4. Karşılaştırmalı regresyonlar
- `dev` v1 → v2: değişim +16.7 puan; iyileşen `ADV-006, ADV-009, ADV-014, ADV-022, ADV-033`; gerileyen `—`.
- `dev` v2 → v3: değişim +83.3 puan; iyileşen `ADV-001, ADV-002, ADV-003, ADV-004, ADV-007, ADV-008, ADV-011, ADV-012, ADV-013, ADV-015, ADV-017, ADV-018, ADV-019, ADV-020, ADV-023, ADV-024, ADV-025, ADV-026, ADV-028, ADV-029, ADV-031, ADV-035, ADV-036, ADV-038, ADV-039`; gerileyen `—`.
- `dev` v1 → v3: değişim +100.0 puan; iyileşen `ADV-001, ADV-002, ADV-003, ADV-004, ADV-006, ADV-007, ADV-008, ADV-009, ADV-011, ADV-012, ADV-013, ADV-014, ADV-015, ADV-017, ADV-018, ADV-019, ADV-020, ADV-022, ADV-023, ADV-024, ADV-025, ADV-026, ADV-028, ADV-029, ADV-031, ADV-033, ADV-035, ADV-036, ADV-038, ADV-039`; gerileyen `—`.
- `holdout` v1 → v2: değişim +0.0 puan; iyileşen `—`; gerileyen `—`.
- `holdout` v2 → v3: değişim +80.0 puan; iyileşen `ADV-010, ADV-016, ADV-021, ADV-027, ADV-030, ADV-032, ADV-034, ADV-037`; gerileyen `—`.
- `holdout` v1 → v3: değişim +80.0 puan; iyileşen `ADV-010, ADV-016, ADV-021, ADV-027, ADV-030, ADV-032, ADV-034, ADV-037`; gerileyen `—`.

## 5. Grader testi ve güvenilirlik
- Planlı negatif mutasyon sayısı: **8**. Tanınan hedef hata oranı: **%100.0**.
- İyi kontrol sayısı: **19**. Yanlış alarm oranı: **%0.0**.
- **Sınır:** Bu dar ve el yapımı hata değişiklikleri, tüm olası pazarlama hatalarını kapsamaz. Model tabanlı jüri-insan uyumu **ölçülmedi**. İki uzmanla kör karşılaştırma henüz yapılmadı.
- Kritik hataların tümünü serbest Türkçe metinden tespit etmek bu offline grader ile garanti değildir; anlam değerlendirmesi ve uyuşmazlıklar insan incelemesine gider.

## 6. Maliyet ve operasyon
- Bu demo sürümleri yerel Python kuralları kullandığından **model API maliyeti 0 USD**. Gerçek Madset/LLM adaptörü henüz bağlı değildir.
- Koşu JSON/CSV içinde süreler milisaniye ve model/kurallar/rubric/grader sürümleri kaydedilir.
- Tek komutla tekrar üretim için `python -m madset_eval demo --out outputs/demo` kullanılır.

## 7. Açık kalanlar — canlı sisteme geçiş kapıları
1. En az iki reklam uzmanının 40 referans beklentiyi kör inceleyerek onaylaması.
2. Serbest doğal dil için kalibre edilmiş LLM grader ya da manuel insan rubriği.
3. Gerçek Advise motoruna yalnız sentetik veri aktaracak bağımsız adapter; gizli cevaplara erişimi olmamalı.
4. Bağımsız test üzerinde yineleme yapılmaması; yeni model sürümleri için yeni kör holdout oluşturulması.
5. Daha geniş zorlayıcı senaryolar, adversarial/metamorfik testler, tekrar denemeleri ve kararlılık ölçümü.
6. Üretim gözlemi ve A/B etkisi doğrulanmadan satış/kârlılık iyileşmesi iddiası kurulamaz.

## 8. Sonuç ve teslimat durumu
**Tamamlanan:** Senaryo sözleşmesi, 30+10 küme, referans etiketleri, üç offline producer, kod tabanlı/heuristic grader, hata mutasyonları, tek komut harness, koşu kayıtları, sürüm karşılaştırma, interaktif olmayan HTML pano, final raporu ve demo.
**Bekleyen doğrulama:** Uzmanlar arası uyum, gerçek LLM jüri kalibrasyonu ve üretim entegrasyon kabulü.

Kaynaklar: Kullanıcının 20 Ekim 2026 tarihli *Advise Lab* PDF’i ve Anthropic *AI ajanları için değerlendirme (eval) rehberi*. Madset’a özgü rubric ve baseline önerileri bunlardan türetilen yerel tasarım kararlarıdır.
