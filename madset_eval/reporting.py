"""Machine-readable report, human-readable HTML dashboard and audit trail."""
from pathlib import Path
import html,json
from .runs import compare

def render_dashboard(runs,calibration,comparisons,location):
    location=Path(location);location.parent.mkdir(parents=True,exist_ok=True)
    colors={'v1':'#AA6554','v2':'#2A6B5A','v3':'#E8A838'}
    css='''body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#F3EBE2;color:#1B2725;margin:0}
    header{background:#1B2725;color:#F3EBE2;padding:32px max(24px,calc((100% - 1100px)/2));}
    main{max-width:1100px;margin:30px auto;padding:0 16px 40px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
    .card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 10px #0000000a}.big{font-size:32px;font-weight:760}
    h1{margin:0 0 8px}h2{margin:28px 0 14px}.muted{color:#65706d}.bar{background:#e9e7e2;border-radius:4px;height:10px;overflow:hidden}
    .fill{height:100%;border-radius:4px}table{width:100%;border-collapse:collapse;background:white;border-radius:10px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f5f5f1}code{font-size:12px;background:#eee;padding:3px 6px;border-radius:4px}small{line-height:1.5}details{margin:12px 0;padding:14px;background:#fff;border-radius:8px}summary{cursor:pointer;font-weight:700}'''
    sections=[]
    for split in ('dev','holdout'):
        rows=[]
        for name in ('v1','v2','v3'):
            run=runs[split][name];s=run['summary'];rate=s['pass_rate']; color=colors[name]
            rows.append(f'<div class="card"><div class="muted">{html.escape(split.upper())} · {name.upper()}</div><div class="big">{rate*100:.1f}%</div><div>Geçiş oranı</div><div class="bar"><div class="fill" style="width:{rate*100}%;background:{color}"></div></div><small>Karar doğruluğu {s["decision_accuracy"]*100:.1f}% · Kritik hata {s["critical_failure_rate"]*100:.1f}% · Ortalama {s["avg_score"]}</small></div>')
        sections.append('<h2>'+split.upper()+' ölçümleri</h2><div class="grid">'+''.join(rows)+'</div>')
    comparison_rows=[]
    for x in comparisons:
        comparison_rows.append(f'<tr><td>{html.escape(x["split"])} {x["from"]} → {x["to"]}</td><td>{x["from_pass"]*100:.1f}%</td><td>{x["to_pass"]*100:.1f}%</td><td>{x["pass_delta"]*100:+.1f} puan</td><td>{html.escape(", ".join(x["regressions"]) or "—")}</td></tr>')
    entries=[]
    for split in ('dev','holdout'):
        rows=runs[split]['v3']['results']
        fail=[r for r in rows if not r['grade']['passed']]
        for row in fail:
            msg=(row['output'].get('recommendation') or '')
            entries.append(f'<tr><td>{row["scenario_id"]}</td><td>{html.escape(split)}</td><td>{html.escape(str(row["output"].get("decision")))}</td><td>{html.escape("/".join(row["grade"]["expected_decisions"]))}</td><td>{row["grade"]["score"]}</td><td>{html.escape(", ".join(row["grade"]["critical_codes"]))}</td><td>{html.escape(msg)}</td></tr>')
    body=''.join(sections)
    body+='<h2>Sürüm karşılaştırmaları</h2><table><thead><tr><th>Kıyas</th><th>Eski</th><th>Yeni</th><th>Fark</th><th>Gerileyen senaryolar</th></tr></thead><tbody>'+''.join(comparison_rows)+'</tbody></table>'
    body+=f'<h2>Grader güvenilirlik kontrolü (sentetik mutasyon)</h2><div class="grid"><div class="card"><div class="muted">Mutasyon yakalama</div><div class="big">{calibration["detection_rate"]*100:.0f}%</div><small>n={calibration["negative_mutations"]} tasarlanmış hatalı örnek</small></div><div class="card"><div class="muted">Yanlış alarm</div><div class="big">{calibration["false_positive_rate"]*100:.0f}%</div><small>n={calibration["positive_controls"]} iyi kontrol</small></div></div>'
    body+='<h2>V3 başarısız senaryolar</h2><div style="overflow:auto"><table><thead><tr><th>ID</th><th>Set</th><th>Karar</th><th>Beklenen</th><th>Puan</th><th>Hata</th><th>Öneri</th></tr></thead><tbody>'+''.join(entries or ['<tr><td colspan="7">Bu test kümesinde V3 başarısızlığı kaydedilmedi.</td></tr>'])+'</tbody></table></div>'
    body+='<details><summary>Önemli metodolojik sınırlamalar</summary><p>Bu sonuçlar üç basit yerel kural örneğine aittir, Madset üretim motorunun ölçümü değildir. Deterministik kontroller doğal dildeki her gizli anlamı doğrulayamaz. Mutasyon kontrolü dar kapsamlıdır; iki bağımsız uzman etiketi ve model yargıç uyumu henüz yoktur. Holdout sonuçları yalnızca final doğrulama için kullanılmalıdır.</p></details>'
    content='<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Madset Eval — Offline Dashboard</title><style>'+css+'</style></head><body><header><h1>MADSET · ADVISE EVAL LAB</h1><div>Sentetik senaryolar · Ölçümlü yerel örnek sürümler · Raporlama</div></header><main>'+body+'</main></body></html>'
    location.write_text(content,encoding='utf-8')
    return str(location)

def render_report(runs,calibration,comparisons,path):
    lines=['# MADSET — Advise Lab Değerlendirme Raporu',
     '', '## 1. Yönetici özeti',
     'Bu rapor **canlı Madset ürününü değil**, 40 sentetik girdide çalıştırılan üç yerel kural tabanlı demo üreticisini (v1/v2/v3) ölçer.',
     'Öneri motoruna platform API erişimi verilmedi, reklam üzerinde işlem yapılmadı ve gerçek müşteri verisi kullanılmadı.',
     'Bu çalıştırma **ürün kalitesi kanıtı** değildir; uçtan uca değerlendirme altyapısının teknik gösterimidir.',
     '', '## 2. Veri kümesi ve yöntem',
     '- Geliştirme: 30 senaryo; bağımsız holdout: 10 senaryo (%25).',
     '- Her vakada beklenen karar kümesi üretimden **önce** dosyaya yazıldı.',
     '- Holdout beklentileri üreticiye verilmedi; yalnız puanlama aşamasında açıldı.',
     '- Rubric: yedi ağırlıklı boyut (toplam 100); geçme: en az 80, kabul edilen karar, sıfır doğrulanmış kritik hata.',
     '- Çıktı JSON sözleşmesi ve aritmetik kontroller deterministik; açık uçlu nitelik puanlaması **heuristic**, uzman onayı gerekir.',
     '', '## 3. Üç sürümün gerçek çalıştırma sonuçları',
     '| Set | Sürüm | Geçti | Karar doğruluğu | Kritik hata oranı | Ortalama skor |',
     '|---|---|---:|---:|---:|---:|']
    for split in ('dev','holdout'):
        for ver in ('v1','v2','v3'):
            s=runs[split][ver]['summary']
            lines.append(f'| {split} | {ver} | {s["passed"]}/{s["trials"]} ({s["pass_rate"]*100:.1f}%) | {s["decision_accuracy"]*100:.1f}% | {s["critical_failure_rate"]*100:.1f}% | {s["avg_score"]:.2f} |')
    lines+=['', 'Birinci sürümde tıklama ağırlıklı acele aksiyonlar, ikinci sürümde zaman/ölçüm kontrolleri, üçüncü sürümde bağlam ve dönüşüm hunisi kontrolleri eklendi. Bu sürümler demo algoritmalarıdır.',
    '', '## 4. Karşılaştırmalı regresyonlar']
    for c in comparisons:
        lines.append(f'- `{c["split"]}` {c["from"]} → {c["to"]}: değişim {c["pass_delta"]*100:+.1f} puan; iyileşen `{", ".join(c["improvements"]) or "—"}`; gerileyen `{", ".join(c["regressions"]) or "—"}`.')
    lines+=['', '## 5. Grader testi ve güvenilirlik',
     f'- Planlı negatif mutasyon sayısı: **{calibration["negative_mutations"]}**. Tanınan hedef hata oranı: **%{calibration["detection_rate"]*100:.1f}**.',
     f'- İyi kontrol sayısı: **{calibration["positive_controls"]}**. Yanlış alarm oranı: **%{calibration["false_positive_rate"]*100:.1f}**.',
     '- **Sınır:** Bu dar ve el yapımı hata değişiklikleri, tüm olası pazarlama hatalarını kapsamaz. Model tabanlı jüri-insan uyumu **ölçülmedi**. İki uzmanla kör karşılaştırma henüz yapılmadı.',
     '- Kritik hataların tümünü serbest Türkçe metinden tespit etmek bu offline grader ile garanti değildir; anlam değerlendirmesi ve uyuşmazlıklar insan incelemesine gider.',
     '', '## 6. Maliyet ve operasyon',
     '- Bu demo sürümleri yerel Python kuralları kullandığından **model API maliyeti 0 USD**. Gerçek Madset/LLM adaptörü henüz bağlı değildir.',
     '- Koşu JSON/CSV içinde süreler milisaniye ve model/kurallar/rubric/grader sürümleri kaydedilir.',
     '- Tek komutla tekrar üretim için `python -m madset_eval demo --out outputs/demo` kullanılır.',
     '', '## 7. Açık kalanlar — canlı sisteme geçiş kapıları',
     '1. En az iki reklam uzmanının 40 referans beklentiyi kör inceleyerek onaylaması.',
     '2. Serbest doğal dil için kalibre edilmiş LLM grader ya da manuel insan rubriği.',
     '3. Gerçek Advise motoruna yalnız sentetik veri aktaracak bağımsız adapter; gizli cevaplara erişimi olmamalı.',
     '4. Bağımsız test üzerinde yineleme yapılmaması; yeni model sürümleri için yeni kör holdout oluşturulması.',
     '5. Daha geniş zorlayıcı senaryolar, adversarial/metamorfik testler, tekrar denemeleri ve kararlılık ölçümü.',
     '6. Üretim gözlemi ve A/B etkisi doğrulanmadan satış/kârlılık iyileşmesi iddiası kurulamaz.',
     '', '## 8. Sonuç ve teslimat durumu',
     '**Tamamlanan:** Senaryo sözleşmesi, 30+10 küme, referans etiketleri, üç offline producer, kod tabanlı/heuristic grader, hata mutasyonları, tek komut harness, koşu kayıtları, sürüm karşılaştırma, interaktif olmayan HTML pano, final raporu ve demo.',
     '**Bekleyen doğrulama:** Uzmanlar arası uyum, gerçek LLM jüri kalibrasyonu ve üretim entegrasyon kabulü.',
     '', 'Kaynaklar: Kullanıcının 20 Ekim 2026 tarihli *Advise Lab* PDF’i ve Anthropic *AI ajanları için değerlendirme (eval) rehberi*. Madset’a özgü rubric ve baseline önerileri bunlardan türetilen yerel tasarım kararlarıdır.']
    Path(path).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return str(path)
