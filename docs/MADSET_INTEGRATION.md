# Gerçek Madset Öneri Motoru Entegrasyonu

## Amaç

Eval laboratuvarı gerçek Madset'in **öneri üreten okuma yolunu** sentetik senaryolarla ölçer. Reklam duraklatma, yeniden başlatma, bütçe artırma, yayınlama veya müşteri verisi okuma yolları eval sırasında çalıştırılmaz.

## Madset tarafında gereken uç

Önerilen iç servis sözleşmesi:

```http
POST /internal/eval/advise
Authorization: Bearer <eval-scope-token>
X-Madset-Eval: synthetic
X-Madset-Dry-Run: true
Content-Type: application/json
```

İstek:

```json
{
  "mode": "eval",
  "dry_run": true,
  "synthetic": true,
  "scenario": {"sector":"...","metrics":{}},
  "constraints": {
    "advice_only": true,
    "forbid_platform_writes": true,
    "forbid_customer_data": true
  }
}
```

Yanıt doğrudan eval çıktı şeması olabilir veya `recommendation` alanında taşınabilir. Servis ayrıca `model`, `model_version`, `prompt_version` ve `usage` metaverisini döndürmelidir. `write_performed=true` dönen yanıt adapter tarafından reddedilir.

## Güvenlik sınırları

1. Endpoint yalnız sentetik payload kabul etmeli; marka, kullanıcı, reklam hesabı veya Meta nesne ID'si istememeli.
2. Endpoint'in kullandığı kimlik/rol Meta write izinlerine sahip olmamalı.
3. Madset'in `pause`, `restart`, `raise_budget`, `publish` ve benzeri işlem fonksiyonları bu çağrı grafiğine dahil edilmemeli.
4. Eval tokenı ayrı scope, ayrı log ve mümkünse ayrı staging ortamında tutulmalı.
5. Gold beklentiler ve senaryo ID'si Madset'e gönderilmemeli.
6. Dönen sayısal `claims` yalnız istekteki metriklerden veya doğrulanabilir türetmelerden gelmeli.

## Çalıştırma

PowerShell:

```powershell
$env:MADSET_ADVISE_URL='https://staging.example.com/internal/eval/advise'
$env:MADSET_EVAL_TOKEN='yalniz-eval-scope-token'
python -m madset_eval run --model external --adapter examples.madset_adapter:advise --split dev --trials 1 --out outputs/madset_real_v1
```

Önce tek vaka için bir smoke komutu, sonra 30-vaka dev çalıştırması yapılmalıdır. Prompt/kurallar dev üzerinde sabitlendikten sonra yeni ve hiç açılmamış bir holdout yalnız bir kez çalıştırılır.

## Gerçek bağlantı için hâlâ bilinmesi gerekenler

- Madset backend deposunun veya staging servisinin erişim adresi.
- Öneri üreten mevcut fonksiyon/route adı.
- Kimlik doğrulama biçimi ve yalnız eval yetkili token üretimi.
- Mevcut Madset yanıtının alanları; gerekirse `_normalize` eşlemesi buna göre düzenlenir.
- Gerçek motorun model, prompt ve kural sürümlerini nereden verdiği.

Bu bilgiler olmadan canlı endpoint'e güvenli biçimde çağrı yapmak doğru değildir; adapter ve sözleşme hazırdır, gerçek route eşlemesi Madset backend bilgisi geldiğinde tamamlanır.
