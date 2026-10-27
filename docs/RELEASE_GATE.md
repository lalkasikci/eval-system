# Yayın Kapısı — Kabul Kontrol Listesi

**Lab uygulaması** ile **üretim için kullanılabilir Advise motoru** iki ayrı statüdür.

| Şart | İlk paket | Açıklama |
|---|---|---|
| Ayrı repo, tek komut | ✅ | `python -m madset_eval demo` |
| API anahtarsız test | ✅ | `unittest` ve offline baseline |
| En az 40 sentetik vaka | ✅ | 30 geliştirme + 10 bağımsız test |
| Beklentiler ilk üretimden önce | ✅ | Senaryo kaynak paketinde önceden yazılı |
| 7 rubric boyutu + F kodları | ✅ | Dokümante, ön sürüm |
| Grader hata yakalama / yanlış alarm ölçümü | ✅ | 8 sentetik mutasyon, 19 pozitif kontrol, **dar örneklem** |
| Model yargıç tekrar güvenilirliği | ✅ | 3 koşu; 27/30 oybirliği, ortalama ikili anlaşma %93,33, Fleiss kappa 0,6625 |
| Model yargıç insan kalibrasyonu | ⏳ | İki kör uzman etiketiyle semantik doğruluk/yanlış alarm henüz ölçülmedi |
| Tek komutta değerlendirme, kayıt ve karşılaştırma | ✅ | JSON, CSV, HTML, Markdown |
| İsimleri görünen regresyonlar | ✅ | `compare()` ve dashboard |
| Model/versiyon/maliyet meta verisi | ✅ | Yerel maliyet 0; Claude 90-yargı tahmini 1,451913 USD, tarife kaynağı ve tarihi kayıtlı |
| 3 ölçülmüş iterasyon | ✅ | Üç örnek kural motoru; **üretim motoru değil** |
| Son sürüm ilkinden iyi (holdout) | ✅ | Yeni 12-vaka kör sette V1 %0, V3 %75; set final koşudan sonra tüketildi |
| Sonuç raporu ve 15 dk demo | ✅ | `FINAL_REPORT.md` + `DEMO_15_MINUTES.md` |
| İki bağımsız uzman onayı | ⏳ | Gerçek insan çalışma gerektirir |
| Türkçe anlam/öneri doğruluğu | ⏳ | Heuristik grader tek başına yeterli değil |
| Gerçek Madset adapteri | ⏳ | Üretim kodu verilmedi; örnek adaptör var |
| Stokastik LLM yargıç tutarlılığı | ✅ | Üç tekrar üzerinden ölçüldü; değişken vakalar raporlandı |
| Canlı ürün etkisi | ⏳ | Canlı veri/gerçek motor olmadan ölçülemez |

**Sonuç:** Advise Lab'in çalışan mühendislik iskeleti ve yeni kör doğrulaması tamamlandı. Canlı Madset sisteminin güvenle dağıtıma alınması için insan uzman etiketi, gerçek Madset adapteri ve üretim etkisi doğrulaması hâlâ dış kapıdır. Demo pass oranı üretim başarısı değildir.
