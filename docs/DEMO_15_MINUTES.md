# Madset Advise Lab — 15 dakikalık canlı demo

**0:00–2:00 / Başlangıç:** `README.md` ve `DECISIONS.md`; laboratuvarın sentetik, tavsiye-only, bağımsız olduğunu anlat.

**2:00–4:00 / Veri kümesi:** `scenario_index.csv`; 30 geliştirme ve 10 ayrı test; örnek ADV-002'de 6.500 TL/26 satış = 250 TL satış CPA; bilinmeyen marj/kâr ayrımını göster.

**4:00–5:00 / Şema testi:** `python -m madset_eval validate`.

**5:00–7:00 / Grader self-test:** `python -m unittest discover -s tests -v` ve `python -m madset_eval calibrate`; genel doğru-karar metninin artık geçmediğini, 19 iyi örneği ve F01–F08 mutasyonlarını göster.

**7:00–10:00 / Tek komut eval:** `python -m madset_eval demo --out outputs/demo`. Üç demo sürümünün dev ve holdout sonuçlarını göster. Çalışma offline ve API maliyeti 0.

**10:00–12:00 / Rapor:** `outputs/demo/DASHBOARD.html` dosyasını tarayıcıda aç; ardından saklı `outputs/blind_v2/regraded/` kayıtlarında V1 %0 ve V3 %75 kör sonucu ile ADV-041/044/049 hatalarını göster. Kör seti yeniden çalıştırma.

**12:00–13:00 / Tekrar deneme:** `python -m madset_eval run --model v3 --split dev --trials 3 --out outputs/repeat`; `observed_pass_at_k` ve `observed_pass_pow_k` farkını anlat.

**13:00–14:00 / Uzman süreci:** `outputs/expert_review_BLIND_V2.csv` paketini göster; senaryo ve öneri metinlerinin bulunduğunu, sürüm/skorun değerlendiriciden gizlenmesi gerektiğini ve henüz gerçek puan verilmediğini söyle.

**14:00–15:00 / Açık riskler:** Gerçek Madset adapteri, uzman uyumu, LLM judge, yeni kör holdout ve canlı etki yok. “Demo puanı, üretim başarısının kanıtı değildir” vurgusuyla kapat.
