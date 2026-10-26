# Madset — Aksiyon Backend Entegrasyon Sözleşmesi

Bu doküman **uygulama taslağıdır**, mevcut backend'in bu uçları sağladığını doğrulamaz. Yeni API yolu veya Meta entegrasyonunun hazır olduğunu varsaymayın.

## Sağlam güvenlik sınırı
- İstemci **asla** Meta'ya doğrudan istek göndermemeli. Yazma sadece Madset backend'inde olmalı.
- Müşteri, marka, reklam hesabı ve ad/campaign/adset sahipliği **sunucu tarafında** doğrulanmalı.
- Değişiklik öncesi müşteri onayı, güncel server-side durum ve idempotency anahtarı tutulmalı.
- Aktif durum ve bütçe Madset arayüzünden değil, **Meta API'sinden tekrar okunarak** doğrulanmalı; yalnızca başarı mesajı yeterli değildir.
- İşlem başarısızsa arayüz ilk durumu başarıymış gibi değiştirmemeli; geri alım/audit trail gerekir.

## Üç yazma eylemi
| action_id | Tetikleyen finding | Yazma davranışı | Doğrulama |
|---|---|---|---|
| pause_ad | Yok | Ad status `PAUSED` | Meta ad effective/config status readback |
| restart_ad | Yok | Campaign + AdSet + Ad active olması gereken durum | Üç nesnenin gerçek durumlarını yeniden oku |
| raise_budget_10 | winner_underfunded, scaling_ready | Bütçenin mevcut sahibi campaign veya adset objesinde %10 artış | Yeni budget değeri ve nesne id readback |

`raise_budget_10` yalnızca data gate açıksa buton ile uygulanabilir. Gate kapalıysa `winner_underfunded → /control-panel`, `scaling_ready → /publish` yönlendirmesi yapılmalı.

## Teklif/onay modeli
1. Backend reklam hesabı ve izinleri kontrol eder.
2. Bütçeyi sahibi olan gerçek nesneden okur, geçerli minimum/birimle %10 artış değerini üretir.
3. İstemci güncel tutar → önerilen tutarı ve `budget_owner` bilgisini gösterir.
4. Kullanıcı onaylar; backend güncel tutarı yeniden kontrol edip *yalnız onaylanan sürümü* yazar (stale state varsa yeniden onay ister).
5. Meta'dan yeniden okunan durum arayüzde gösterilir. Hata varsa geri bildir ve başarısız olarak kaydet.

## Eylem tipleri
- `navigate`: mevcut web rotasına yönlendirme, platforma yazma yok.
- `follow`: kullanıcının seçtiği tarihle backend'de takip kaydı (prototipte yalnız localStorage).
- `info`: düğmesiz kart.

## Öneri vs. yazma ayrımı
Advise öneri üretimi ve eval testleri **yazma yapmaz**. Meta güncellemesi ayrı müşteri-onaylı operasyon katmanı olmalıdır. Deneme veri setleri ile production reklam nesneleri karışmamalıdır.
