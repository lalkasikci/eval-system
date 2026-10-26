# MADSET — Senaryo Veri Sözleşmesi v1.0

**Aşama 2 teslimi.** `data/dev/scenarios.json` ve `data/holdout/inputs.json` doğrulaması için `contracts.validate_input` çalışır. Her senaryo sentetiktir. v1 veri kümesi `meta | google`, `TRY` ve `current | stale` ile sınırlıdır; kapsamı genişletmeden yeni platform para birimi uydurulmaz.

## Girdi alanları

| Alan | Tip | Anlam | Durum |
|---|---|---|---|
| `synthetic` | true | Gerçek müşteri kullanılmadığı teminatı | Zorunlu |
| `sector` | string | Anonim sektör | Zorunlu |
| `platform` | `meta/google` | Platforma özgü hedef/operasyon | Zorunlu |
| `objective` | string | Hedef (lead, leads, messages, sales, calls) | Zorunlu |
| `campaign_age_days` | integer >= 0 | Kampanya yaşı | Zorunlu |
| `observation_window_days` | integer >= 0 | Değerlendirilen gözlem süresi | Zorunlu |
| `currency` | TRY | Harcama/gelir para birimi | Zorunlu |
| `metrics` | object | Sayısal reklam ve sonuç verileri | Zorunlu |
| `availability` | object | Ölçülme durum bayrakları | Zorunlu |
| `data_freshness` | current/stale | Güncel veya eski kayıt | Zorunlu |
| `context` | string | Kapasite, kampanya süreci ve olası ölçümleme riskleri | Zorunlu |

## Metrik alanları

`spend`, `impressions`, `clicks` zorunlu ve negatif olamaz. `leads`, `appointments`, `sales`, `revenue`, `target_cost_per_result` null olabilir. Sayılar sentetiktir; marka, e-posta, telefon, kişi adı veya reklam hesabı ID içermez.

`availability.sales_measured` false ise `sales = null` olmalıdır. True ise satış sayısı bilinmek zorundadır (`0` meşru ve doğru bir sonuç olabilir). Benzer koşul `appointments_measured` ve `appointments` için geçerlidir. Null = bilinmiyor. Başarısız API okuması `data_freshness=stale` ile işaretlenebilir; sıfıra çevrilmez.

### Matematik

- Tıklama oranı `ctr_pct = clicks / impressions * 100`.
- Tıklama başı maliyet `cpc = spend / clicks`.
- Talep başı maliyet `cpl = spend / leads`.
- Randevu başı maliyet `cpa_appointment = spend / appointments`, ancak randevu ölçülüyorsa.
- Satış başı maliyet `cpa_sale = spend / sales`, ancak satış ölçülüyorsa.
- Atfedilebilir ciro/harcama `roas = revenue / spend`, ancak ciro ölçülebiliyorsa ve harcama pozitifse.
- Payda `null` veya sıfırsa oran `null` döner. Sıfır harcamada ROAS = 0 değil **hesaplanamaz**.
- Brüt ciro net kâr değildir; iade, komisyon, hammadde ve işçilik gibi maliyetler eksikse kâr iddiası yoktur.
- Reklam hedefi başka olduğunda `lead` ve `sales` aynı sonuç birimi değildir; platformlar/para birimleri doğrudan toplama konusu olamaz.

## Etiketler ve holdout ayrımı

`dev/scenarios.json` dosyası 30 adet `{id, group, input, expectation}` kaydı taşır. Her `expectation` önceden yazılmış `allowed_decisions`, `must_include`, `must_not_include`, `critical_fails` (izlenecek F-kod kataloğu) ve `reference_rationale` içerir. Bu öğelerin tümü otomatik anlam testi olarak uygulanmış değildir.

`holdout/inputs.json` dosyasında ilk 10, `holdout_v2/inputs.json` dosyasında sonradan dondurulan 12 `{id, group, input}` bulunur; altın beklentiler kendi `private/gold.json` dosyalarında saklanır. **Generator yalnızca `input` alır; `scenario_id` bile gönderilmez.** Hash'ler `data/manifest.json` tarafından doğrulanır. Gold dosyasının aynı diskte bulunması mutlak erişim izolasyonu değildir; gerçek harici adapter için OS/container sınırı ayrıca kurulmalıdır.

Senaryoların tamamı ilk kaynak paketten korunmuştur; burada sayı uydurularak yeniden yazılmamıştır. Referans etiketler **uzman tarafından onaylanmamış taslaklardır**. Bu sınırlama kaldırılmadan “nihai stratejik doğruluk” ilan edilmez.
