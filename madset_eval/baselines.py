"""Three deliberately simple, offline baseline policies. NOT production advertising advice.

These baselines get ONLY the input, with scenario id and gold labels stripped.
They are development exemplars, not a trained LLM or a validated ad strategy.
"""
from __future__ import annotations
from .contracts import derived_metrics

def has_any(text,*patterns):
    return any(pattern in text for pattern in patterns)

def make_result(decision, inp, *, recommendation, rationale, next_step, uncertainty='', risk='', action_type='observe', multiplier=None, measures=('spend','clicks')):
    m=inp['metrics'];dm=derived_metrics(inp);ev=[];claims={}
    for key in measures:
        value = m.get(key) if key in m else dm.get(key)
        if value is not None:
            val=round(value,2) if isinstance(value,(int,float)) else value
            ev.append({'key':key,'value':val})
            claims[key]=val
    action={'type':action_type}
    if multiplier is not None:action['budget_multiplier']=multiplier
    return {'decision':decision,'recommendation':recommendation,'rationale':rationale,
        'next_step':next_step,'uncertainty':uncertainty,'risk':risk,'evidence':ev,'claims':claims,'action':action}

def v1(inp):
    # Weak early baseline: clicks are mistakenly treated as indication of success.
    m=inp['metrics']
    if m['clicks']>500:
        return make_result('ACT',inp,recommendation='Tıklamalar var; bütçeyi artırın.',rationale='Çok tıklama aldınız.',next_step='Bütçeyi %50 artırın.',action_type='increase_budget',multiplier=1.5)
    return make_result('MAINTAIN',inp,recommendation='Reklamınız iyi gidiyor.',rationale='Veri normal görünüyor.',next_step='İzleyin.')

def v2(inp):
    m=inp['metrics'];dm=derived_metrics(inp);ctx=inp['context'].casefold()
    if inp['data_freshness']=='stale' or any(p in ctx for p in ('gönderilmiyor','iki kere','eşleştirme yok','senkronunu','webhooku yok','güncellenmedi')):
        return make_result('MEASURE',inp,recommendation='Önce sonuç takibini doğrulayın.',rationale='Ölçümleme eksik veya güvenilir değil.',next_step='Veri kaynağını kontrol edin.',uncertainty='Satış sonucunu bu veriden bilemeyiz.',action_type='audit_tracking')
    if inp['campaign_age_days']<=4:
        return make_result('WAIT',inp,recommendation='Bu reklama hemen müdahale etmeyin.',rationale='Kampanya yeni, kıyas için erken.',next_step='Birkaç gün sonra tekrar ölçün.',uncertainty='Düşük örneklem karar için yeterli değil.')
    target=m.get('target_cost_per_result')
    observed=dm['cpl'] if m.get('leads') is not None else dm['cpa_sale']
    if target and observed is not None and observed > target:
        return make_result('DIAGNOSE',inp,recommendation='Sonuç başı maliyet hedefin üzerinde.',rationale='Maliyet farkının nedenini araştırın.',next_step='Dönüşüm adımlarını inceleyin.',uncertainty='Kesin neden henüz doğrulanmadı.',risk='Bütçe artışını erteleyin.',action_type='audit_funnel',measures=('spend','clicks','cpl' if m.get('leads') is not None else 'cpa_sale'))
    return make_result('MAINTAIN',inp,recommendation='Mevcut ayarları koruyun.',rationale='Kısa vadede zorunlu değişiklik görünmüyor.',next_step='Sonuçları izleyin.',uncertainty='Gerçek kârlılık bu veriden kesinleşmez.')

def v3(inp):
    m=inp['metrics'];dm=derived_metrics(inp);ctx=inp['context'].casefold();age=inp['campaign_age_days'];target=m.get('target_cost_per_result')
    measures=('spend','clicks')
    if m['spend']==0:
        return make_result('WAIT',inp,recommendation='Henüz reklam harcaması ve dağıtım yok.',rationale='Harcama sıfırken sonuç maliyetini yorumlamak doğru olmaz.',next_step='Reklam yayını ve ilk gösterimleri kontrol edin.',uncertainty='Maliyet oranı hesaplanamaz.',risk='Veri oluşmadan performans kararı vermeyin.',measures=('spend','impressions','clicks'))
    if inp['data_freshness']=='stale':
        return make_result('MEASURE',inp,recommendation='Veri güncelliğini düzeltmeden karar vermeyin.',rationale='Mevcut sayılar eski bir kayıt olabilir.',next_step='Veri akışını yeniden doğrulayın.',uncertainty='Güncel performans bilinmiyor.',risk='Eski veriye dayanarak bütçeyi değiştirmeyin.')
    measurement=has_any(ctx,'gönderilm','ölçülm','takip kapalı','olay','webhook','tekilleştir','senkron','null','bağlanma bilgisi','dönüşüm sayısı farklı')
    if measurement and not (age<=4 and inp['objective']=='calls'):
        if has_any(ctx,'iki kere','duplicate','tekilleştir','dönüşüm sayısı farklı'):
            return make_result('MEASURE',inp,recommendation='Önce attribution ve yinelenen olayları tekilleştirerek ölçümü doğrulayın.',rationale='Çift ya da farklı tanımlı dönüşümler gerçek sonucu şişirebilir.',next_step='Olay kimliklerini, attribution penceresini ve tekilleştirmeyi kontrol edin.',uncertainty='Doğrulanana kadar satış CPA hesabı güvenilir değildir.',risk='Tekrarlı kayıtları ayrı satış kabul etmeyin.')
        if inp['objective']=='calls':
            return make_result('MEASURE',inp,recommendation='Telefon tıklaması ile tamamlanan gerçek görüşmeyi ayrı ölçün.',rationale='Call-click bir görüşmenin bağlandığını veya müşteri oluştuğunu kanıtlamaz.',next_step='Çağrı bağlanma ve nitelikli görüşme takibini doğrulayın.',uncertainty='Gerçek görüşme sayısı bilinmiyor.',risk='Tıklamaları müşteri olarak saymayın.')
        if has_any(ctx,'crm','null'):
            return make_result('MEASURE',inp,recommendation='CRM ve sonuç entegrasyonunu düzeltmeden performans kararı vermeyin.',rationale='Null sonuç sıfır başarı değildir; senkron eksikliği sonucu gizliyor olabilir.',next_step='CRM senkronunu ve olay akışını uçtan uca doğrulayın.',uncertainty='Randevu veya satış sonucu bilinmiyor.',risk='Eksik sonucu sıfır kabul ederek reklamı durdurmayın.')
        return make_result('MEASURE',inp,recommendation='Önce Purchase/sonuç olay akışını ve entegrasyonu doğrulayın.',rationale='Eksik veya tutarsız takip gerçek sonucu gizleyebilir.',next_step='Olayları, veri akışını ve platform eşleşmesini kontrol edin.',uncertainty='Ölçülmeyen sonuç sıfır değildir.',risk='Ölçüm onarılmadan harcama artışı önermeyin.')
    if age <= 4:
        if inp['objective']=='calls':
            return make_result('WAIT',inp,recommendation='Bu kısa dönemde telefon tıklamasını gerçek görüşme veya müşteri saymayın.',rationale='Üç günlük örneklem ve call-click verisi karar için sınırlı.',next_step='Birkaç gün daha bekleyip bağlanan çağrı ve rezervasyonları takip edin.',uncertainty='Gerçek görüşme sonucu henüz bilinmiyor.',risk='Tıklamaya bakarak bütçeyi değiştirmeyin.',measures=('spend','clicks'))
        return make_result('WAIT',inp,recommendation='Bu kısa döneme bakarak reklamı değiştirmeyin.',rationale='Gözlem süresi ve örneklem henüz sınırlı.',next_step='Daha fazla talep ve birkaç günlük eğilimi takip edin.',uncertainty='İlk günlerin performansı kalıcı sonuç göstermez.',risk='Gereksiz durdurma ve agresif değişiklikten kaçının.',measures=('spend','clicks','leads'))
    # Broad business signals are used instead of scenario-specific phrases or IDs.
    if has_any(ctx,'doluluk','kapasite') and has_any(ctx,'dolu','sınırlı','boş tarih'):
        return make_result('ACT',inp,recommendation='Bütçeyi büyütmek yerine boş tarih ve kapasiteye dönük küçük bir test yapın.',rationale='Talep maliyeti iyi ancak mevcut kapasite neredeyse dolu.',next_step='Boş günler için kontrollü teklif ve kitle testi planlayıp maliyet eşiğini takip edin.',uncertainty='Ek satışın kârlılığı bilinmiyor.',risk='Dolu kapasiteye sınırsız talep satın almayın.',action_type='test_offer',measures=('spend','leads','cpl'))
    if has_any(ctx,'yüksek niyet','gerçek telefon','üretim kapasitesi','ölçekleme için alan','talebi karşılayabilir'):
        focus='sorgu ve saat' if inp['objective']=='calls' or inp['platform']=='google' else 'hedef kitle ve teklif'
        return make_result('ACT',inp,recommendation=f'İşe yarayan {focus} bölümünü sınırlı bir testle geliştirin.',rationale='Mevcut kanıt ve operasyonel koşullar kontrollü deney için uygun.',next_step='Önceden tanımlı maliyet eşiğiyle küçük bir test başlatın ve gerçek sonucu takip edin.',uncertainty='Ek bütçenin getirisi garanti değildir.',risk='Testte zarar sınırı belirleyin.',action_type='test_offer',measures=('spend','leads' if m.get('leads') is not None else 'clicks','cpl' if m.get('leads') is not None else 'cpc'))
    if has_any(ctx,'önceki dönem','bütçeli','harcama fark','dönem karşılaştır'):
        return make_result('WAIT',inp,recommendation='Farklı bütçeli dönemlerin satış sayılarını tek başına karşılaştırmayın.',rationale='Harcama farkı normalizasyonu etkiler.',next_step='Aynı harcama ve dönem koşullarında oranları izleyin.',uncertainty='Hacim farkı tek başına performans düşüşü değildir.',risk='Yetersiz kıyasa dayanarak reklamı değiştirmeyin.',measures=('spend','sales','cpa_sale'))
    if has_any(ctx,'iptal','tamamlanan sipariş'):
        return make_result('DIAGNOSE',inp,recommendation='Brüt ve net satışları ayırıp iptal/iade nedenlerini inceleyin.',rationale='Brüt satın alma sayısı net tamamlanan sipariş sayısı değildir.',next_step='İptal oranını ve net satış başı maliyeti karşılaştırın.',uncertainty='Net gelir ve kâr henüz kesin değil.',risk='Brüt satışı net başarı gibi raporlamayın.',action_type='audit_funnel',measures=('spend','sales','cpa_sale'))
    if has_any(ctx,'mevzuat','hassas','uygunluk'):
        return make_result('DIAGNOSE',inp,recommendation='Kampanya değişikliğini mevzuat ve platform uygunluk kontrolüne bağlayın.',rationale='Hassas alanda performans kadar iddia ve hedefleme uygunluğu da doğrulanmalıdır.',next_step='Metin, hedefleme ve teklifleri uygunluk kontrolünden geçirin.',uncertainty='Uygunluk doğrulanmadan sonuç vaat edilemez.',risk='Garanti veya uygunsuz sağlık/hukuk iddiası kullanmayın.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if has_any(ctx,'ücretli müşteri','deneme kayd'):
        return make_result('DIAGNOSE',inp,recommendation='Deneme kaydı ile ücretli müşteri dönüşümünü ayrı değerlendirin.',rationale='Kayıt hacmi tek başına ücretli dönüşüm değildir.',next_step='Denemeden ücretliye geçiş oranını ve kayıp adımını inceleyin.',uncertainty='Ücretli müşteri sonucu mevcut veriden kesinleşmiyor.',risk='Tüm kayıtları müşteri saymayın.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if has_any(ctx,'bölge','lokasyon'):
        return make_result('DIAGNOSE',inp,recommendation='Bölgesel performansı ayırmadan bütçe ölçeklemeyin.',rationale='Bölgelerin ayrı sonuçları bilinmeden toplam ortalama yanıltabilir.',next_step='Her bölge için maliyet ve gerçek dönüşümü karşılaştırın.',uncertainty='Hangi bölgenin daha verimli olduğu bilinmiyor.',risk='İki bölgeyi eşit dönüşümlü varsaymayın.',action_type='audit_funnel',measures=('spend','leads' if m.get('leads') is not None else 'sales'))
    if has_any(ctx,'büyük satış','tekil','aykırı'):
        return make_result('DIAGNOSE',inp,recommendation='Dağılımı ve tekil büyük satışın ortalamaya etkisini inceleyin.',rationale='Tek bir yüksek değer güvenilir ve kalıcı ortalama oluşturmaz.',next_step='Medyan sipariş değerini ve satış dağılımını karşılaştırın.',uncertainty='ROAS benzer biçimde devam etmeyebilir.',risk='Aykırı satışa dayanarak bütçeyi büyütmeyin.',action_type='audit_funnel',measures=('spend','sales','roas'))
    if has_any(ctx,'etkinlik','son tarih','yarın'):
        return make_result('DIAGNOSE',inp,recommendation='Zaman kısıtı ile rezervasyon dönüşümünü birlikte inceleyin.',rationale='Kısa süre, yeni reklamın sonucu etkinliğe yetiştirmesini belirsiz kılar.',next_step='Mevcut rezervasyon hunisini ve kalan süreyi kontrol edin.',uncertainty='Yeni reklamın zamanında sonuç vereceği garanti değildir.',risk='Yetişmeyecek talep için kontrolsüz bütçe harcamayın.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if has_any(ctx,'checkout','ödeme'):
        return make_result('DIAGNOSE',inp,recommendation='Ürün sayfası, checkout ve ödeme adımlarındaki kaybı inceleyin.',rationale='Trafik ile satış arasındaki ödeme hunisinde sorun olabilir.',next_step='Sayfa, sepet ve ödeme dönüşümlerini ayrı karşılaştırın.',uncertainty='Kesin neden henüz kanıtlanmadı.',risk='Yalnız CPM veya tıklamayı sebep ilan etmeyin.',action_type='audit_funnel',measures=('spend','sales','cpa_sale'))
    if has_any(ctx,'arama terim','sorgu','anahtar kelime'):
        return make_result('DIAGNOSE',inp,recommendation='Arama terimleri, teklif ve sorgu-lead uyumunu inceleyin.',rationale='Hacim ile lead kalitesi aynı şey değildir.',next_step='Sorguları nitelikli sonuç ve maliyetle karşılaştırın.',uncertainty='Sorunun tek bir anahtar kelimeden geldiği kanıtlanmadı.',risk='Tüm sorgulara otomatik bütçe artışı uygulamayın.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if 'mesaj' in ctx and has_any(ctx,'kayıt','dönüşüm','sahte'):
        return make_result('DIAGNOSE',inp,recommendation='Teklif ve mesajdan kayıt/satış dönüşümünü inceleyin.',rationale='Mesaj hacmi tek başına ticari sonuç değildir.',next_step='Mesaj kalitesi ve kayıt dönüşümünü ayrı izleyin.',uncertainty='Tüm mesajların sahte veya değerli olduğu söylenemez.',risk='Mesajları doğrudan satış saymayın.',action_type='audit_funnel',measures=('spend','leads' if m.get('leads') is not None else 'clicks'))
    if has_any(ctx,'düşük nitelik','lead kalit','talep kalit'):
        return make_result('DIAGNOSE',inp,recommendation='Lead miktarı ile niteliğini ve takip kanalını ayrı inceleyin.',rationale='Düşük CPL tek başına iş sonucu değildir.',next_step='Nitelikli görüşme ve satışa geçiş oranını karşılaştırın.',uncertainty='Ucuz leadlerin kârlılığı bilinmiyor.',risk='Yalnız ucuz lead için bütçeyi artırmayın.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if has_any(ctx,'marj','roas','kâr') and dm.get('roas') is not None:
        return make_result('DIAGNOSE',inp,recommendation='ROAS ile kârlılığı ayırıp maliyet ve marjı inceleyin.',rationale='Ciro/harcama oranı birim maliyetleri içermez.',next_step='Marj, iade ve operasyon giderleriyle net katkıyı hesaplayın.',uncertainty='ROAS tek başına kârı kanıtlamaz.',risk='ROAS 1 üzerinde diye kârlı ilan etmeyin.',action_type='audit_funnel',measures=('spend','revenue','roas'))
    if has_any(ctx,'gerçek sıfır','sıfır talep','form entegrasyonu sağlam'):
        return make_result('DIAGNOSE',inp,recommendation='Ölçüm doğrulanmış gerçek sıfır sonucu kabul edip huni ve teklifi inceleyin.',rationale='Bu durumda sıfır, null veya eksik ölçüm değildir.',next_step='Gösterimden forma kadar huni kırılımını kontrol edin.',uncertainty='Kesin neden henüz belirlenmedi.',risk='Sıfırı ölçüm arızası sanıp görmezden gelmeyin.',action_type='audit_funnel',measures=('spend','leads','cpl'))
    if (m.get('leads') is not None and m['leads']>0 and m.get('appointments') is not None and m['leads']>=20 and m['appointments']/m['leads']<0.1):
        return make_result('DIAGNOSE',inp,recommendation='Talep çok ama randevuya dönüşüm zayıf; müşteri takip sürecini inceleyin.',rationale='Talep sayısı tek başına ticari başarı değil.',next_step='Yanıt hızı ve nitelikli görüşme oranını karşılaştırın.',uncertainty='Kayıp nedeni henüz belirlenmedi.',risk='Bu veriye dayanarak bütçeyi artırmayın.',action_type='audit_funnel',measures=('spend','leads','appointments','cpl'))
    obs=dm['cpl'] if m.get('leads') is not None else dm['cpa_sale']
    if obs is not None and target is not None and obs>target:
        focus='arama terimleri, teklif ve lead kalitesini' if inp['platform']=='google' and m.get('leads') is not None else 'ürün sayfası, sorgu uyumu ve satış dönüşümünü' if inp['platform']=='google' else 'reklam mesajı, sayfa ve takip akışını'
        return make_result('DIAGNOSE',inp,recommendation='Sonuç maliyeti hedefin üzerinde; önce nedenini ayrıştırın.',rationale='Birim sonuç maliyeti hedefi aşıyor.',next_step=f'{focus} inceleyin.',uncertainty='Sorunun kaynağı kesinleşmedi.',risk='Kontrolsüz harcama artışından kaçının.',action_type='audit_funnel',measures=('spend','leads' if m.get('leads') is not None else 'sales','cpl' if m.get('leads') is not None else 'cpa_sale'))
    return make_result('MAINTAIN',inp,recommendation='Mevcut reklamı koruyup hedef sonuç maliyetini düzenli izleyin.',rationale='Lead/satış maliyeti hedefle uyumlu; değişiklik için açık kanıt yok.',next_step='Sonuç maliyetini ve gerçek talep, randevu veya satış ilerleyişini kaydedin.',uncertainty='Satış, marj ve kârlılık ölçülmüyorsa ayrıca doğrulanmalıdır.',risk='Sırf tıklama arttı diye bütçeyi agresif büyütmeyin.',measures=('spend','leads' if m.get('leads') is not None else 'sales','cpl' if m.get('leads') is not None else 'cpa_sale'))

BASELINES={'v1':v1,'v2':v2,'v3':v3}
