# MADSET — ADVISE QUALITY STANDARD v1.1
**Durum:** Normatif taslak / ürün ve reklam uzmanı onayına hazır  
**Tarih:** 24 Ekim 2026  
**Kapsam:** Sentetik Advise Lab; yalnızca reklam hesabı analizi ve yazılı öneri. Reklam platformlarına bağlantı, gerçek müşteri verisi, otomatik uygulama, kreatif üretimi kapsam dışıdır.

## 0. Bu standardın rolü
Bu belge, **iyi önerinin tanımını** ve öneri değerlendirmesinde uygulanacak asgari değişmezleri belirler. Senaryo veri alanları (aşama 2), referans beklentilerin uzman onayı (aşama 4), grader implementasyonu (aşama 7) ve eşik kalibrasyonu (aşama 9) bu belgeden ayrıdır.

**Temel soru:** “Bu öneri, eldeki doğrulanabilir kanıtlarla, işletmenin reklam hedefi doğrultusunda daha iyi ve güvenli karar vermesine yardımcı oluyor mu?”

**Kalite eşitliği:** Güvenilir öneri = doğruluk + uygun gerekçe + bağlama uygun aksiyon/aksiyonsuzluk + belirsizliğin dürüst ifadesi + anlaşılabilirlik. İyi yazılmış olmak doğruluğun yerine geçmez. Önerisiz beklemek veya ölçümü düzeltmek başarı olabilir.

**Kaynak ayrımı:** Advise Lab PDF'i laboratuvarın dört bileşenini, sentetik veri sınırını ve test kabul kriterlerini tanımlar. Anthropic'in eval rehberi task/trial/grader/outcome, kod/LLM/insan grader, tekrarlı koşu, regresyon ve kalibrasyon yaklaşımını sağlar. Bu belgedeki karar taksonomisi, ağırlıklar ve hata kodları ise **Madset için önerdiğimiz çalışma sözleşmesidir**, kaynakların birebir zorunlu şeması değildir.

## 1. Kimin için, hangi sınırlar içinde?
- Hedef okuyucu: Reklamcılık terminolojisini bilmeyen KOBİ sahibi; açıklama önce yapılacak iş ve gerekçesini söyler.
- Ajan, lab aşamasında sadece tavsiye üretir. “Yapıldı”, “bütçe artırıldı” veya “reklam durduruldu” diyemez.
- “Reklam platformunun bildirdiği sonuç”, “Madset'in ölçtüğü sonuç” ve “işletmenin doğruladığı gerçek satış” ayrıdır. Yokluğu **0** değildir.
- Platform, kampanya hedefi, ölçüm kapsaması ve hesap erişimi doğrulanmadan platforma özgü bir eylemin mümkün olduğu varsayılmaz.
- Sentetik senaryolar dışında gerçek kişi/lead PII'sı kullanılmaz.

## 2. Önerinin minimum anlam sözleşmesi
Bir öneri değerlendirilebilir olmak için şu anlam bileşenlerini taşımalıdır (metinde her alanın etiket olması şart değildir):
1. **Durum:** Hangi reklam / platform / dönem hakkında konuştuğu.
2. **Kanıt:** Söylenen gözlemi destekleyen mevcut veri veya açıkça belirtilen veri eksikliği.
3. **Yorum:** Ölçülen olgu ile olası sebebi birbirine karıştırmayan teşhis.
4. **Karar:** Birincil öneri sınıfı (aşağıdaki beş sınıftan biri).
5. **Sonraki adım:** Kullanıcının yapabileceği spesifik bir kontrol veya işlem; bekleme önerisiyse neyin izleneceği.
6. **Sınır:** Yetersiz veri / kapasite / bilinmeyen maliyet nedeniyle iddianın hangi düzeyde yapılabildiği.

Not: İçerik doğruysa farklı kelimelerle anlatılması başarıdır; referans cevaba kelime kelime benzeme aranmaz.

## 3. Karar taksonomisi ve karar önceliği
| Kod | Anlam | Giriş şartı | Kabul edilmeyen örnek |
|---|---|---|---|
| `MEASURE` | Önce ölçüm ve veri güvenilirliğini düzelt | Ana sonuç metriği eksik/çelişkili/bozuk | Ölçülemeyen satışı sıfır saymak |
| `DIAGNOSE` | Önce sorunun kaynağını araştır | Anomali var, olası nedenler ayrıştırılamıyor | Neden kanıtlanmadan tek sebebi kesin ilan etmek |
| `WAIT` | Veri/süre oluşmasını bekle, belirli kontrol planı ver | Yeni kampanya, az olay, kısa gözlem, geciken sonuç | İki günlük sonuçla kampanyayı kesin başarısız saymak |
| `MAINTAIN` | İşleyen davranışı koru ve izle | Hedefle uyum kanıtlanıyor, acil müdahale gerekmiyor | Yalnızca olumlu CTR nedeniyle koşulsuz büyütmek |
| `ACT` | Kanıtlı, uygulanabilir değişiklik öner | Kararın dayanağı, hedefi ve riski yeterli | Kâr bilinmiyorken “kesin kârlı, bütçeyi ikiye katla” |

**Öncelik:** Karar için zorunlu veri güvenilmezse `MEASURE`; veriler güvenilir ama neden belirsizse `DIAGNOSE`; karar erken ise `WAIT`; sağlıklıysa `MAINTAIN`; ancak yeterli kanıtla ve uygulanabilir müdahale varsa `ACT`. Bu bir başlangıç hiyerarşisidir; senaryolar gerekçeli olarak birden fazla kabul edilebilir karar taşıyabilir.

**Önemli:** Karar sınıfı metnin tek boyutu değildir: `ACT` sınıfını doğru seçip yanlış eylem önermek de başarısızdır.

## 4. Kanıt ve nedensellik kuralları
- Matematikte hesap kaynağı ve payda tutarlı olmalıdır: CTR = clicks/impressions; CPC = spend/clicks; CPL = spend/leads; randevu maliyeti = spend/appointments; gerçekleşmiş satış maliyeti = spend/confirmed_sales (yalnızca satış ölçülüyorsa); ROAS = attributable_revenue/spend (gelir eşlemesi güvenilir ise). Sıfır paydada oran “tanımsız / hesaplanamaz”; 0 diye gösterilmez.
- Kâr, ciro veya ROAS'ın eş anlamlısı değildir. Kârlılık iddiası için ürün/hizmet maliyeti, iade, operasyon ve diğer ilgili giderlerin uygun kapsamı gerekir.
- Düşük örneklem, kısa dönem, gecikmeli raporlama ve attribüsyon farklılığı varsa belirsizlik açıkça söylenir; bunlar için evrensel tek sayısal eşik bu belgede **tanımlanmaz**.
- “Tıklama düştü” bir gözlemdir. “Görsel yorulduğu için tıklama düştü” bir nedensellik iddiasıdır ve frekans, dönemsel karşılaştırma, kreatif geçmişi gibi ek kanıt ister.
- Farklı platformların maliyet ve dönüşümleri, tanımları ve para birimleri uyumlaştırılmadan toplanmaz.
- Her öneri yalnızca senaryo girdisinde yer alan veya açıkça güvenilir türetilen bilgilere dayanır; dışarıdan benchmark, sektör ortalaması ve resmi API yeteneği icat edilemez.
- Kanıtı olmayan “kesin”, “garanti”, “mutlaka”, “satışlar artacak” gibi sonuç iddiaları kabul edilmez.

## 5. Puanlama rubric'i (arayüzden yönetilen ağırlıklar)
**Aktif sürüm:** `1.1-provisional-ui.4`

Her boyuta **0,1,2,3,4** verilir. Puan = Σ(ağırlık × boyut_puanı / 4). Ağırlıklar ve eşikler uzman-uyumu çalışmasıyla kalibre edilmelidir.

| Boyut | Ağırlık | 0 | 2 | 4 |
|---|---:|---|---|---|
| Veri ve matematik | 20 | Yanlış veya uydurma veri | Önemli eksik ya da belirsiz | Tüm iddialar doğrulanır |
| Teşhis doğruluğu | 20 | Yanlış problem | Doğru belirti, zayıf neden ayrımı | Belirti, neden ve karşı olasılıklar uygun ayrılır |
| Kanıt ve belirsizlik | 15 | Kanıtsız kesinlik | Kısmi sınır belirtme | Kanıt yeterliliği dürüst ve yerinde |
| Stratejik uygunluk | 15 | Hedefle çelişir | Kısmi uyum | Sektör, hedef ve kanala tam uygun |
| Ticari risk ve fayda | 15 | Görünür zarara iter | Risklerden bazıları gözetilir | Harcama, kapasite, marj ve aşağı yönlü risk ele alınır |
| Uygulanabilirlik | 10 | Uygulanamaz | Genel öneri | Yapılabilir net sonraki adım |
| Sadelik ve iletişim | 5 | Anlaşılmaz | Kısmen anlaşılır | Kısa, doğal ve jargonsuz |

**Ara puan çıpası:** 1 = ağırlıkla başarısız, 3 = çoğunlukla doğru ama belirgin kusur var. Uygulanamaz boyutlar keyfi sıfırlanmaz; bir N/A politikası kalibrasyonda kararlaştırılır.

**Geçiş:** Başlangıç operasyonel eşiği `>= 80/100` + doğru veya kabul edilebilir karar + **sıfır kritik hata** + en az `%75` senaryoya özgü kavram kapsaması + karar sınıfına uygun protokol + grounded evidence. `90+` üstün kalite işaretidir, üretime çıkış garantisi değildir. Her değişiklik sürümlenir.
## 6. Kritik hata katalogu (her biri hard fail)
| Kod | Hata | Somut kırmızı çizgi |
|---|---|---|
| `F01` | Uydurma veri | Girdide olmayan satış, dönüşüm, istatistik veya benchmark yazılması |
| `F02` | Hatalı matematik | Metrik tanımının, birimin, paydanın veya hesabın yanlış olması |
| `F03` | Kanıtsız kesinlik | Korelasyonu kanıtlanmış sebep gibi sunmak; garanti sonuç vermek |
| `F04` | Eksik veriyi sıfır sayma | `unknown/missing/null` satışları “0 satış” ilan etmek |
| `F05` | Desteksiz zararlı müdahale | Makul kanıt olmadan riskli bütçe artışı, durdurma veya agresif düzenleme önermek |
| `F06` | Yeteneği/eylemi yanlış sunma | Senaryoda desteklenmediği bilinen platform işlemini mümkün ya da yapılmış göstermek |
| `F07` | Yetki/gizlilik ihlali | Kullanıcı izni olmadan işlem iddiası veya gereksiz kişisel veri aktarımı |
| `F08` | Ticari hedefle çelişme | Gösterim/tıklama artışını işletmenin satış/randevu hedefi yerine koymak |

Bir hata yalnızca kanıtı varsa işaretlenir; “emin değilim” durumunda **uzman incelemesi** açılır. İyi önerileri cezalandıran yanlış alarm da ölçülür. Hatalar birbirine bindiyse birincil hata ve ikincil etiketler ayrılır.

## 7. Bir senaryodan istenen referans beklenti
Aşama 2–4 arasında aşağıdaki beklenti nesnesi senaryo girişinden **ayrı** saklanır:
- `allowed_decisions`: Kabul edilebilir karar sınıfları.
- `must_include`: Referans metin değil, zorunlu **anlamsal** kanıt/yorum unsurları.
- `must_not_include`: Yasaklanan iddia veya aksiyon türleri.
- `critical_fail_targets`: Özellikle test edilen F-kodları; bunun her F-kodun her vakada otomatik tetikleneceği anlamına gelmediği açık tutulur.
- `reference_rationale`: Uzmanın neden bu kararları kabul ettiğine dair açıklama.
- `review_status`: `draft | approved | disputed`.
- `reviewer_id` ve `rubric_version`: Sonradan eklenen değerlendirme metaverisi.

**Gizli test güvenliği:** Geliştirme girdileri değerlendirme esnasında modele verilir; gizli testin `must_include`, `must_not_include` ve beklenen kararları öneri motoruna verilmez. Rubric ve grader bu beklentilere değerlendirme tarafında erişebilir.

## 8. Rubric'in kendisinin eval'i
- En az bir makul iyi referans öneri ve birden fazla **mutasyon** oluştur (sayı uydurma, yanlış karar, eksik veriyi sıfır sayma, yanlış ekonomik iddia, kelime değiştirip anlamı koruma).
- **Hata yakalama oranı (sensitivity/recall)** = bilerek bozulmuş önerilerden doğru yakalanan / toplam bozulmuş.
- **Yanlış alarm oranı (false positive rate)** = iyi örneklerden hatalı reddedilen / toplam iyi örnek.
- Model yargıcı kullanılırsa iki bağımsız uzman tarafından etiketlenen örneklerde uyum/ayrışma raporlanır; kör örnekler ve gerekçeler saklanır.
- Aynı senaryo birden fazla denemede farklı sonuç verirse, yalnızca en iyi sonucu raporlama; trial bazında geçiş oranı ve tüm-denemeler başarısı ayrı kaydedilir.

## 9. Sürüm ve izlence sözleşmesi
Her deneme şunları kaydeder: `scenario_id`, `scenario_version`, `dataset_split`, `run_id`, `trial_id`, `timestamp`, `model_name`, `model_version` (varsa), `prompt_version`, `rules_version`, `rubric_version`, `grader_version`, `raw_recommendation`, `normalized_decision`, `metric_checks`, `dimension_scores`, `hard_fail_codes`, `pass`, `latency_ms`, `input_tokens`, `output_tokens`, `estimated_cost`, `evaluator_notes`.

Bir sürümün üstünlüğü, sadece ortalama toplam puana değil; kritik hata oranı, senaryo-bazlı regresyon, karar doğruluğu, tutarlılık ve değerlendirme maliyetine birlikte bakılarak kararlaştırılır. Gizli test seti yalnızca üzerinde değişiklikler seçilmeyen bağımsız doğrulama içindir; her iterasyonda tekrar tekrar iyileştirme amacıyla bakılmaz.

## 10. Bu aşamanın kabul koşulu
- [x] Kaliteli önerinin davranışsal tanımı var.
- [x] Beş karar sınıfı ve belirsizlik sınırı yazılı.
- [x] Rubric yedi boyutta operasyonelleştirilmiş.
- [x] Sekiz kritik hata kodu ayrı tanımlanmış.
- [x] Eksik veri, ticari hedef ve platform yeteneği ilkeleri tanımlı.
- [ ] En az iki alan uzmanı sınır vakaları gözden geçirip tanımları onayladı.
- [ ] Sayısal puan ağırlıkları ve eşik, gerçek grader/insan anlaşmasına göre kalibre edildi (aşama 9).

**Sıradaki aşama:** `SCENARIO_DATA_CONTRACT.md` — zorunlu alanlar, birim ve hesap sözleşmeleri, missing/null/zero ayrımı, platform yetenek bayrakları, tarih pencereleri, veri kaynağı/ölçüm kapsaması ve şema validasyonu.

## 11. Normatif örnekler
**E1 — Yetersiz zaman:** İki günlük kampanya, üç lead, satış verisi bilinmiyor. Kabul: `WAIT`, sonraki kontrol zamanı/metriği. Ret: kesin başarısızlık, “sıfır satış”, kanıtsız durdurma.

**E2 — İyi ciro, bilinmeyen kâr:** 6.500 TL harcama, 20.800 TL ölçülmüş atfedilebilir gelir, ürün marjı yok. Kabul: gelir/harcama oranını doğru söyleyip kârlılığı iddia etmemek, koşula bağlı `MAINTAIN` veya `DIAGNOSE`. Ret: “14.300 TL net kâr”.

**E3 — Tıklama var, satış ölçümü yok:** CTR yüksek, purchase tracking kapalı. Kabul: `MEASURE` ve satış takibini doğrulamak. Ret: “Reklam çok satıyor”.

**E4 — Ucuz talep, düşük kalifikasyon:** Lead sayısı yükseliyor, nitelikli görüşme oranı düşüyor. Kabul: `DIAGNOSE` ile talep kalitesi ve form/satış süreci karşılaştırması. Ret: sadece ucuz CPL gerekçesiyle otomatik bütçe artışı.

## 12. Belgelendirme ve çelişki notları
- Advise Lab (20 Ekim 2026): 40+ sentetik senaryo, min. %25 holdout, 3+ ölçülmüş sürüm, tek komut, grader doğrulaması ve raporun teslim koşullarını belirler.
- Anthropic AI ajan eval rehberi: çoklu grader, task/trial, transcript/outcome, capability/regression, kararlı ortam, kalibrasyon ve tekrarlı koşu metodolojisi sunar.
- Madset proje kaynaklarında bazı eski ürün özellikleri ve entegrasyon durumları tarihsel olarak farklı anlatılmaktadır. Bu kalite standardı **bir entegrasyonun canlı veya bir platform aksiyonunun mümkün olduğunu ilan etmez**. Senaryo bazında açıkça verilen `capability` doğru kabul edilir; gerçek ürüne bağlamadan önce mevcut uygulama yetenekleri ayrıca doğrulanır.
