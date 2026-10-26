# Claude API ile Madset Eval çalıştırma

## 1. Bilgisayarına Python 3.10+ kur

Paketin ana klasörünü terminalde aç. Üçüncü taraf Python paketi gerekmez.

## 2. Anahtarı güvenli biçimde tanımla

**macOS / Linux, Terminal:**

```bash
export ANTHROPIC_API_KEY='KENDI_API_KEYIN'
```

**Windows PowerShell (önerilen; anahtar görünmez ve diske yazılmaz):**

```powershell
.\scripts\run_claude_judge.ps1
```

Betik anahtarı gizli giriş olarak ister, yalnız alt süreçte kullanır ve tamamlandığında ortamdan temizler. Anahtarı sohbet, kaynak kodu, `.env.example`, ekran görüntüsü veya GitHub'a yazma.

Bu güvenli betik mevcut en yeni `v3_dev` transcriptini Claude LLM yargıcıyla yeniden puanlar. Böylece öneri üretmek için ayrıca API çağrısı yapılmaz.

## 3. Önce ücretsiz yerel doğrulama

```bash
python -m madset_eval validate
python -m unittest discover -s tests -v
```

## 4. Gerçek Claude API ile deneme (ücretli çağrılar)

```bash
python -m madset_eval run --model external --adapter examples.claude_adapter:advise --split dev --trials 1 --out outputs/claude_v1
```

Bu komut 30 geliştirme senaryosu için 30 Claude API çağrısı yapar. İlk kez deniyorsan az sayıda çağrı isteyen `python scripts/smoke_claude.py` komutunu kullan; 1 API isteği yapar.

Yalnız LLM yargıcını elle çalıştırmak için, anahtarı mevcut terminal oturumunda güvenli biçimde tanımladıktan sonra:

```bash
python -m madset_eval regrade outputs/demo/runs/V3_RUN.json --judge-adapter examples.claude_judge:judge --out outputs/claude_judge
```

İsteğe bağlı model değişikliği:

```bash
export ANTHROPIC_MODEL='claude-sonnet-4-6'
```

## 5. Bağımsız test (son aşama)

```bash
python -m madset_eval run --model external --adapter examples.claude_adapter:advise --split holdout --trials 3 --out outputs/claude_holdout
```

Bağımsız test beklentilerini model girdisine katma. Holdout'a her prompt denemesinde bakıp prompt ayarlama (test setini kirletir).

## 6. Dikkat edilmesi gereken sınırlar

- Bu entegrasyon Claude ile **gerçek öneri üretir**, mevcut grader ise **offline heuristik**tir, uzman onaylı tam semantik değerlendirme değildir.
- Dış API erişimi ve maliyet gerekir. API anahtarın yoksa yerel testler çalışır, Claude çağrısı çalışmaz.
- Fiyat değişkenleri verilmezse dış adapter maliyeti `null` raporlar; bu durumda gerçek maliyet için sağlayıcının usage/billing kayıtlarını kullanın.
- Adapter token sayılarını ve gerçek yanıt modelini kaydeder. Maliyeti otomatik hesaplamak için çalıştırma anındaki sağlayıcı fiyatlarını `ANTHROPIC_INPUT_USD_PER_MTOK` ve `ANTHROPIC_OUTPUT_USD_PER_MTOK` ortam değişkenleriyle sabitleyin; değer verilmezse maliyet dürüstçe `null` kalır.
- `outputs/claude_v1` altındaki eski örnek koşu API anahtarı olmadığı için 30/30 producer error ile bitmiştir; başarılı Claude ölçümü değildir.
- Senaryo verileri sentetiktir. Gerçek reklam hesabına ya da platform API'sine bağlanmaz.
- Birden fazla deneme daha fazla API çağrısı ve harcama yaratır.
- Anahtarın çoklu workspace gerektiriyorsa `ANTHROPIC_WORKSPACE_ID` da ayarlanmalıdır.

## Dosyalar

- `examples/claude_adapter.py`: gerçek Claude API bağlantısı
- `scripts/smoke_claude.py`: tek senaryo denemesi
- `data/dev/scenarios.json`: 30 geliştirme girdisi ve beklentisi
- `data/holdout/inputs.json`: 10 gizli test girdisi
- `data/holdout/private/gold.json`: yalnız grader'ın okuyacağı gizli beklentiler
