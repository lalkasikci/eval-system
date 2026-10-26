# MADSET — Advise Eval Lab v1.0

**Çalışır, çevrimdışı sentetik reklam tavsiyesi değerlendirme laboratuvarı.** Bu arşiv bir SaaS kurulumu veya gerçek Meta/Google hesabı entegrasyonu değildir. Gerçek müşteri, marka ve kişi verileri kullanılmaz; reklam yaratılmaz, değiştirilmez, yayınlanmaz.

## 1 dakikada çalıştır

Gereksinim: **Python 3.10+**. Üçüncü taraf paket, API anahtarı, veritabanı, ağ bağlantısı gerekmez. Proje kökünde:

```bash
python -m unittest discover -s tests -v
python -m madset_eval validate
python -m madset_eval demo --out outputs/demo
```

Demo tamamlandığında:

- `outputs/demo/DASHBOARD.html` — tarayıcıda açılabilen **yerel HTML** pano (ağ bağlantısı gerekmez).
- `outputs/demo/FINAL_REPORT.md` — sayısal ilk/son sürüm raporu, hata ve limitler.
- `outputs/demo/SUMMARY.json` — makine okuyabilir metrikler, sürüm karşılaştırmaları, grader testi.
- `outputs/demo/runs/*.json` — her öneri, karar, gerekçe, kritik hata, puan, model/kurallar ve süre izleri.
- `outputs/demo/runs/*.csv` — Excel/BI için sonuç tabloları.

## İşletime yönelik komutlar

```bash
python -m madset_eval run --model v3 --split dev --trials 3 --out outputs/runs
python -m madset_eval run --model v3 --split holdout --trials 3 --out outputs/final_holdout
python -m madset_eval calibrate --out outputs/grader_calibration.json
python -m madset_eval compare outputs/runs/V1.json outputs/runs/V2.json
python -m madset_eval regrade outputs/runs/V1.json --out outputs/regraded
```

`compare` komutundaki `V1.json` ve `V2.json` yer tutucudur: `run` çıktısında yazılan gerçek adları kullanın. Karşılaştırma artık her senaryonun bütün trial geçiş oranlarını kullanır. `regrade`, kayıtlı sentetik girdi ve çıktıları üreticiyi yeniden çağırmadan yeni grader sürümüyle puanlar.

### İsteğe bağlı Claude LLM yargıç

Kod tabanlı matematik ve kritik hata denetimleri korunurken Claude, yedi rubric boyutunun anlamsal değerlendirmesini yapabilir. Anahtarı dosyaya veya komut geçmişine yazmadan mevcut bir geliştirme koşusunu değerlendirmek için Windows PowerShell'de:

```powershell
.\scripts\run_claude_judge.ps1
```

Betik anahtarı görünmeyen bir giriş alanında ister, yalnızca alt Python sürecine `ANTHROPIC_API_KEY` olarak aktarır ve işlem bitince bellek/ortam değişkenini temizler. Varsayılan olarak en yeni `v3_dev` kaydındaki **tek senaryoyu** bağlantı/maliyet güvenliği için değerlendirir ve her çağrıda ilerleme gösterir. Başarılı kontrolden sonra `-Limit 30` ile 30 benzersiz senaryo çalıştırılabilir. Sonuçlar her çağrıdan sonra `outputs/claude_judge/` altında kısmi olarak saklanır; hata sonrası `-Limit 30 -Resume` yalnız tamamlanmamış senaryolardan devam eder. Claude sonucu tek başına yayın kararı değildir; insan etiketleriyle kalibrasyon yapılana kadar `provisional` kabul edilir.

Tamamlanan örnek koşuda Claude Sonnet 4.6, 30 V3 geliştirme önerisinin 25'ini geçirdi (%83,33); karar türlerinin 30'u da doğru ve kritik hata sayısı sıfırdı. Ortalama puan 91,04; kullanım 57.952 girdi ve 20.395 çıktı tokenı; ortalama yargıç gecikmesi 13,89 saniyeydi. Fiyatlar sabitlenmediği için maliyet `null` kaydedildi. Ayrıntılar `docs/FINAL_REPORT.md` ve `docs/GRADER_AND_CALIBRATION.md` içindedir.

**Holdout setini iterasyon amacıyla tekrar tekrar test etmeyin.** İlk 10 vakalık holdout ve 12 vakalık `holdout_v2` final doğrulamada kullanılmış ve tüketilmiştir. Yeni üretici/prompt sürümleri için yeni, hash ile dondurulmuş bir kör set oluşturun.

### Madset'in GERÇEK öneri motorunu bağlama

Güvenli HTTP adapteri hazırdır. Madset tarafında yalnız öneri üreten, sentetik veri kabul eden ve platform yazmalarını kapatan bir `dry_run` endpoint'i gerekir:

```bash
export MADSET_ADVISE_URL='https://staging.example.com/internal/eval/advise'
export MADSET_EVAL_TOKEN='eval-scope-token'
python -m madset_eval run \
  --model external --adapter examples.madset_adapter:advise \
  --split dev --trials 1 --out outputs/madset_real_v1
```

`examples/madset_adapter.py` yalnız **sentetik girdiyi** gönderir; `id`, `group`, `expectation`, `must_include`, `allowed_decisions` ve gizli test dosyası servise gitmez. `pause`, `restart`, `raise_budget` ve `publish` gibi gerçek yazma işlemleri bu endpoint'in kimliğinde ve çağrı grafiğinde kapalı olmalıdır. Ayrıntılı sözleşme: `docs/MADSET_INTEGRATION.md`.

**Asgari JSON çıktı biçimi:**

```json
{
  "decision": "WAIT",
  "recommendation": "Kampanya iki günlük, hemen değiştirmeyin.",
  "rationale": "Dönem kısa; satış takibi bilinmiyor.",
  "next_step": "Üç gün daha gözleyin, gerçek sonucu kontrol edin.",
  "uncertainty": "Satış adedi bilinmiyor.",
  "risk": "Erken bütçe artırmak risklidir.",
  "evidence": [{"key":"spend","value":540}],
  "claims": {"spend":540},
  "action": {"type":"observe"}
}
```

`claims` içindeki her sayı kod ile doğrulanır; `evidence` bu sayılara referans verir. `decision`: `ACT | WAIT | DIAGNOSE | MEASURE | MAINTAIN`. Modelin gerçek çıktısını bu yapıya eşlemek için bir adaptör gerekli olabilir; JSON'a sadece doğru olduğunu doğruladığınız değerleri yazın.

## Proje haritası

| Yol | İçerik |
|---|---|
| `docs/QUALITY_STANDARD.md` | İlk kalite ilkeleri; 7 kriter, 8 kritik hata |
| `docs/SCENARIO_DATA_CONTRACT.md` | Senaryo ve ölçüm sözleşmesi |
| `docs/GRADER_AND_CALIBRATION.md` | Otomatik puanlama, sınırlamalar ve insan doğrulaması |
| `docs/DECISIONS.md` | Advise Lab'deki açık soruların yanıtları ve nedenleri |
| `docs/ITERATIONS.md` | V1, V2, V3 değişiklikleri ve ölçüm kayıtları |
| `docs/EXPERT_REVIEW.md` | İki bağımsız uzmanla kontrol ve görüş ayrılığı süreci |
| `docs/RELEASE_GATE.md` | Yayın öncesi kabul şartları |
| `docs/DEMO_15_MINUTES.md` | 15 dakikalık canlı gösterim sırası |
| `docs/MADSET_INTEGRATION.md` | Gerçek Madset motoru için read-only endpoint ve güvenlik sözleşmesi |
| `data/dev/scenarios.json` | 30 **beklentili** geliştirme senaryosu |
| `data/holdout/inputs.json` | 10 **beklentisiz** test girdisi |
| `data/holdout/private/gold.json` | Sadece değerlendirici tarafındaki 10 gizli beklenti |
| `data/holdout_v2/` | Sonradan dondurulan 12 vakalık kör doğrulama seti; final koşudan sonra tüketildi |
| `madset_eval/` | Şema, üç örnek üretici, grader, harness, mutation eval, raporlama |
| `tests/` | Bağımsız ve API anahtarsız otomatik kontroller; LLM judge sözleşmesi mock testleri |
| `outputs/demo/` | Gerçekten koşturulmuş örnek sonuçlar + pano + rapor |

## İnsan uzman incelemesi

```bash
python -m madset_eval review-export outputs/demo/runs/v3_dev_<gerçek-run-id>.json \
  --out outputs/expert_review.csv
python -m madset_eval review-analyze outputs/expert_review.csv
```

`review-export` iki uzman için **boş** puanlama satırları açar. Dosyaya yazılan uzman yargıları olmadan uzman uyumu veya model-yargıç kalibrasyonu tamamlandı sayılmaz. `review-analyze`, doldurulmuş `overall_pass` üzerinde gözlenen uyumu ve Cohen kappa'yı hesaplar; diğer rubrik boyutları ileride uzman geçerli değerlendirmesi için tutulur.

## Ne ölçülüyor; ne ölçülmüyor?

**Ölçülüyor:** schema bütünlüğü, desteklenen sayısal iddialar, hesaplar, öngörülebilir kritik güvenlik ihlalleri, kabul edilen karar türü, karar-protokolü, senaryoya özgü kavram kapsaması, 7 boyutta başlangıç rubric, tekrarlı deneme tutarlılığı, bütün trial'ları kullanan paired regression, sürüm meta verisi ve grader mutasyon testi.

**Henüz ölçülmüyor:** İnsan uzman konsensüsüyle doğrulanmış tam Türkçe serbest metin semantiği, uzmanlar arası onay, kalibre edilmiş LLM-judge güvenilirliği, canlı müşteri satış lift'i ve gerçek reklam platformlarının desteklenebilirliği. Claude ile bir dev koşusu yapılmış olması bu kalibrasyonun yerine geçmez. Dolayısıyla `passed=true` **"offline otomatik ön kontrolden geçti"** anlamındadır; gerçek ürünün güvenli olduğu onayı değildir.

## Mimari tercih

Tek işlemde kurulabilen, **Python standart kütüphanesiyle** çalışan bir harness seçildi. Dış API veya çatı bağımlılığı test sonucunu değiştirmez. Platform ve üretim modelleri ayrı adaptörle eklenir. Madset'in TypeScript ürün reposuna taşırken aynı JSON sözleşmesi ve altın beklenti etiketleri korunmalıdır.

## Kaynak

- Kullanıcı tarafından sağlanan *Advise Lab — Sentetik Senaryo, Rubric ve Eval Döngüsü*, 20 Ekim 2026. Laboratuvar sınırları ve kabul kriterleri.
- Kullanıcı tarafından sağlanan *AI ajanları için değerlendirme (eval) rehberi* (Anthropic rehberinin Türkçe sunumu). Task/trial/grader, değerlendirici kombinasyonu, tekrarlı koşu, regresyon, kalibrasyon ve gözden geçirme yöntemleri.

Madset'e özgü sayısal puanlar, beş karar sınıfı ve F01–F08 kataloğu, **belgelerin doğrudan içeriği değil, bu laboratuvar için tasarlanan yerel sözleşmelerdir.**
