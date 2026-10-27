# MADSET — Advise Lab Karar Kaydı

**Kaynak:** Advise Lab s.2 “Senin karar vereceğin sorular”. Her kararın gerekçesi ve durumu aşağıdadır. Bu belgede kaynakların yanıtlamadığı noktalar açık yerel tasarım kararıdır.

| # | Soru | Yanıt / karar | Gerekçe ve durum |
|---|---|---|---|
| D1 | Hesabı hangi metrikler anlatır? | Platform, hedef, harcama, gösterim, tıklama, lead, randevu, satış, ciro, hedef maliyet, veri güncelliği, kampanya yaşı, ölçüm bayrakları ve sektör bağlamı | Ürün etkisini yalnız CTR'den çıkarmaz. **Uygulandı.** |
| D2 | İyi öneri nedir? | Doğrulanabilir kanıt + uygun karar + uygulanabilir aksiyon/aksiyonsuzluk + ihtiyat + anlaşılır dil | Madset KOBİ kullanıcısı için güvenilirdir. **Standart taslağı uygulandı, uzman onayı açık.** |
| D3 | Kod mu LLM yargıç mı? | Matematik/yapı kod; tekrarlanan alan kavramları açıklanabilir semantik heuristik; açık uçlu stratejik anlam insan (ileride kalibre edilmiş model jüri) | Tek yöntem yeterli değil. **Kod + kavram kapsaması çalışıyor; insan/LLM kalibrasyon açık.** |
| D4 | LLM yargıca ne kadar güvenilir? | Tekrarlı yargıda anlaşma ölçülür; ardından iki kör uzman etiketiyle false-positive, recall ve insan uyumu hesaplanır | Değerlendiriciyi de değerlendirmek şart. **Aynı 30 öneri üç kez yargılandı: 27/30 oybirliği, ortalama ikili anlaşma %93,33, Fleiss kappa 0,6625. Tekrar tutarlılığı ölçüldü; insan kalibrasyonu hâlâ açık.** |
| D5 | Aynı senaryo iki çalışmada değişirse? | Trial bazında sakla, ortalama/median skor, `observed_pass_at_k` ve `observed_pass_pow_k` hesapla | Tek iyi çıktı güvenilirliği kanıtlamaz. **Uygulandı.** |
| D6 | İki sürümden hangisi daha iyi? | Öncelik sırası: kritik hata, karar tutarlılığı, göreve göre geçiş, eşlenik regresyon, maliyet ve gecikme; tek ortalamayla karar verme | Kullanıcıya zarar verecek tek kritik hata etkili olabilir. **Sürüm kıyas kodu hazır.** |
| D7 | Senaryoyu ezberleme nasıl anlaşılır? | Model üreticiye gold/ID verilmez; hash ile dondurulmuş yeni kör test; metamorfik test, karşı-örnek ve kör güncelleme | İlk 10 holdout tüketildikten sonra 12 yeni vaka finalde bir kez çalıştırıldı. **V3 %75; üç gerçek hata görünür kaldı.** |

## İlave uygulama kararları

- **Teknoloji:** Python standart kütüphanesi. *Neden:* tek komut, anahtarsız test, düşük operasyon yükü, bağımsız repo; Madset'in üretim TypeScript sisteminden bağımsız.
- **Ayrı repo:** Sadece sentetik JSON. Gerçek Meta/Google/OpenAI Ads API çağrısı yok.
- **Öneri etkisi:** Script yalnızca JSON döndürür; platform durumu değiştirmez. ACT kodu **önerilen** aksiyondur.
- **İterasyonlar:** Üç sürüm demo kural motoru; ürünün üretim sürümü değildir. İlk ve son sayısal ölçümler `outputs/demo/SUMMARY.json` kaynaklıdır.
- **Eşikler:** 80/100 ve sıfır kritik hata operasyonel ön-izleme eşiği. İnsan kalibrasyonu olmadan yayına giriş izni vermez.
- **Boş/sıfır:** `null`, `0` ve `stale` ayrı; reklam verilmemesi “CPL 0” değil, oran hesaplanamaz.
- **Holdout etiği:** İlk 10 vaka ve sonradan oluşturulup SHA-256 ile dondurulan 12-vaka `holdout_v2` final çalıştırmalarından sonra tüketilmiştir. Yeni sürümler için yeni gizli vaka kümesi gerekir.
- **Yeniden puanlama:** Grader değişirse üretici yeniden çağrılmaz; kaydedilmiş input/output transcript `regrade` ile puanlanır ve eski kayıt korunur.
- **Tutarlılık:** Demo üreticiler deterministiktir; rassal gerçek modele genelleme yoktur.
