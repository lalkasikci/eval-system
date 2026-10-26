# MADSET — Grader ve Kalibrasyon Sözleşmesi v1.0

**Aşama 6–9 teslimi.** Her tavsiye JSON'a normalize edilir. Puan ve hata kuralları `madset_eval/grading.py` dosyasındadır. `QUALITY_STANDARD.md` normatif bağlamdır.

## Grader türleri

1. **Kod tabanlı (çalışıyor):** Sözleşme geçerliliği, sayısal iddia–gerçek veri karşılaştırması, sıfır/null ayrımı, garanti söylemi için sınırlı ifade kontrolü, yüksek riskli bütçe aksiyonu, kanal uyumsuzluğu, yetkisiz eylem iddiası.
2. **Açıklanabilir semantik heuristik (çalışıyor):** 7 boyutta 0–4 puanlara ek olarak gold `must_include` metninden alan kavramları çıkarılır; çıktıdaki kanıt, karar-protokolü ve kavram kapsaması kaydedilir. Doğru karar etiketi taşıyan genel/geçiştirici metin artık geçemez. Otomatik `80+`, `no hard fail`, en az `%75` kavram kapsaması, karar-protokolü ve grounded evidence yalnızca **offline ön kontrol**dür.
3. **İnsan rubric'i (iş akışı ve form hazır):** İki bağımsız reklam uzmanı, örnekleri görmeden (sürüm/grader puanları maskelenerek) her kategoriye puan verebilir; uyuşmazlıklar uzlaşma listesine gider. Bu inceleme **henüz yapılmadı**.
4. **Model tabanlı jüri (opsiyonel, adaptörü hazır):** `examples.claude_judge:judge` ile Claude yedi rubric boyutunu değerlendirebilir. Gerçek anahtarla ölçüm henüz yapılmadı; iki uzmanla uyum ölçülmeden sonucu kesin kalite kanıtı sayılmaz.

## Kritik hata kuralları

- F01: `claims` içinde gözlemlenmeyen veya bilinmeyen bir metrik ileri sürülmüş.
- F02: Geçerli metrikte yanlış değer/hesap (örn. harcama/satış bölümü).
- F03: Bazı açık ve kesin başarı vaatleri. **“Garanti değildir” geçerli bir ihtiyattır; garanti sayılmaz.** Serbest doğal dilin bütün biçimlerini yakalayamaz.
- F04: Bazı açık ifadelerle ölçülmeyen satışın sıfır iddia edilmesi.
- F05: Ani bütçe değişimi gibi kontrolsüz riskli aksiyon.
- F06: Platforma uygun olmayan işlem türü.
- F07: Yalnızca öneri laboratuvarındayken “işlemi yaptım” demek veya gereksiz PII istemek.
- F08: Tıklama hacmini nihai iş sonucu sayan belirgin ifadeler.
- FMT: Çıktı sözleşmesine uyumsuzluk.

**Not:** Regex ile yanlış/olumsuz formda kurulan iddialar gözden kaçabilir; hard-fail kataloğu semantik bir gerçeği değil tespit algoritmasını temsil eder. Çıktı denetiminde kanıtın kendisi saklanır.

## Pozitif/negatif kontrol

`python -m madset_eval calibrate`: 19 iyi örnek ve 8 hedefli hata mutasyonu (F01–F08) çalıştırır. On dokuzuncu pozitif kontrol, "garanti kullanmayın" uyarısının yanlışlıkla garanti iddiası sayılmasını engelleyen kör-set bulgusudur. Mutasyonlar kodla hazırlanmış olup aynı hatanın farklı yazımlarını sistematik örneklemez. **Yakalama oranı / yanlış alarm oranı yalnız bu dar örneklem için geçerlidir**; uzman etiketlerinin yerini alamaz.

## Kör set bulgusu ve yeniden puanlama

12 vakalık `holdout_v2` üreticiye bakılmadan önce SHA-256 ile donduruldu. V3 ilk koşuda %66,7 geçti. Grader, olumsuz yönergedeki "garanti" sözcüğünü F03 saydığı için bir yanlış alarm bulundu. Üretici tekrar çağrılmadan `regrade` komutuyla aynı transcript grader 1.1 altında yeniden puanlandı ve V3 sonucu %75 oldu. İlk ve yeniden puanlanan kayıtların ikisi de saklanır.

## Karar güvenilirliği

`pass_rate`: başarılı trial / tüm trial. `observed_pass_at_k`: aynı görevin k tekrarından en az biri başarılı olan görev oranı. `observed_pass_pow_k`: k tekrarın hepsinde başarılı olan görev oranı. Bunlar yalnızca örneklem içinde gözlenen oranlardır; stokastik model davranışının gerçek olasılık tahmini değildir. Tekrarlı denemeler aynı başlangıç koşulundan başlatılır.

## Kritik kalite kusuru: skor doygunluğu

Başlangıç heuristiği kısa, düzgün yapılandırılmış ve doğru karar türüne sahip bir öneriye maksimum puan verebilir. Bu, önerinin bütün ticari nüansları doğru değerlendirdiği anlamına **gelmez**. Özellikle küçük ve senaryoları yazan ekipten gelen veri kümesinde aşırı uyum riski yüksektir. Geniş kör set ve uzman yargısı gelene kadar skoru yalnızca regresyon/teknik sinyal olarak kullanın.
## Claude LLM yargıç katmanı

İsteğe bağlı `examples.claude_judge:judge` adaptörü, deterministik hard-check sonuçlarını değiştirmeden yedi rubric boyutunu ve genel anlamsal geçişi Claude ile değerlendirir. Bir hard-check hata kodu varsa LLM yüksek puan verse bile sonuç geçemez. Yargıç model/prompt sürümü, token sayıları, gecikme ve fiyat değişkenleri tanımlıysa maliyet koşu kaydına eklenir.

Bu katman insan uzman etiketleriyle henüz kalibre edilmediğinden sonuçları geçici (`provisional`) kabul edilir. Güvenilirlik iddiası için kör insan etiketlerine karşı agreement, yanlış alarm ve hata yakalama oranı ayrıca ölçülmelidir.

