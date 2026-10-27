"""Transparent offline grader: hard safety rules + heuristic rubric.

This evaluator is intentionally NOT a semantic marketing expert. For broad natural-language
claims, a human (or calibrated LLM) must still review; see docs/GRADER.md.
"""
from __future__ import annotations
import math,re
from .contracts import DERIVED,METRIC_KEYS,WEIGHTS,validate_output,derived_metrics,ContractError
from .rubric import PASS_THRESHOLD

ERRORS={
 'F01':'Unsupported or fabricated numeric claim',
 'F02':'Arithmetic / metric conversion wrong',
 'F03':'Unsupported certainty / guarantee',
 'F04':'Unknown outcome treated as confirmed zero',
 'F05':'Unsupported high-risk change',
 'F06':'Platform-incompatible or unavailable action',
 'F07':'Claimed unapproved action / identifiable private data',
 'F08':'Vanity click metric substituted for business outcome',
 'FMT':'Output violates response contract',
}

# The gold `must_include` entries are short natural-language requirements.  The
# rules below translate recurring domain concepts into auditable phrase groups.
# This is deliberately smaller than a semantic LLM judge, but it prevents a
# generic, well-shaped response from passing merely because its decision label
# is correct.  Human calibration remains the release gate for nuanced meaning.
CONCEPTS={
 'monitor':((r'gözlem',r'izle',r'kaydet'),(r'gözlem',r'izle',r'takip',r'kontrol')),
 'target_cost':((r'hedef',r'maliyet'),(r'hedef',r'maliyet',r'cpl',r'cpa')),
 'cpa_sale':((r'cpa',r'satış başı'),(r'cpa_sale',r'satış başı',r'satış cpa',r'250(?:[.,]0+)?')),
 'cpl':((r'lead maliyet',r'ucuz lead',r'düşük cpl'),(r'cpl',r'lead maliyet',r'talep maliyet',r'sonuç maliyet')),
 'profit_caution':((r'marj',r'kâr',r'karlı',r'kârlı',r'birim kâr'),(r'marj',r'kâr',r'karlı',r'kârlı',r'maliyetler bilin',r'garanti değildir')),
 'time_sample':((r'zaman',r'gün',r'örneklem',r'erken',r'dönem temsil'),(r'zaman',r'gün',r'örneklem',r'erken',r'kısa dönem',r'veri oluş')),
 'call_quality':((r'telefon',r'call-click',r'çağrı'),(r'telefon',r'çağrı',r'görüşme',r'call')),
 'booking_crm':((r'randevu',r'crm'),(r'randevu',r'crm',r'müşteri takip',r'yanıt hızı')),
 'checkout_payment':((r'ödeme',r'checkout'),(r'ödeme',r'checkout',r'satın alma adım')),
 'search_terms':((r'arama terim',r'sorgu'),(r'arama terim',r'sorgu',r'teklif',r'anahtar kelime')),
 'lead_quality':((r'lead kalit',r'talep.*kalit',r'nitelik'),(r'kalit',r'nitelik',r'gerçek talep',r'dönüşüm')),
 'message_conversion':((r'mesaj.*kayıt',r'mesajdan'),(r'mesaj',r'kayıt',r'dönüşüm')),
 'page_query':((r'ürün sayfa',r'sorgu uyum'),(r'ürün sayfa',r'sorgu',r'uyum',r'dönüşüm')),
 'capacity':((r'kapasite',r'dolu'),(r'kapasite',r'dolu',r'boş tarih',r'operasyon')),
 'controlled_test':((r'kontrollü',r'sınırlı',r'deneme',r'test'),(r'kontrollü',r'sınırlı',r'deneme',r'test',r'eşik')),
 'tracking':((r'ölç',r'takip',r'olay akış',r'entegrasyon'),(r'ölç',r'takip',r'olay',r'entegrasyon',r'veri akış')),
 'attribution_dedup':((r'attribution',r'duplicate',r'tekilleştir'),(r'attribution',r'duplicate',r'tekilleştir',r'çift',r'yinelen')),
 'integration_limit':((r'yetenek sınır',r'entegrasyon'),(r'yetenek',r'entegrasyon',r'ölçülem',r'bilinm')),
 'zero_null':((r'null',r'sıfır',r'0 satış',r'gerçek sıfır'),(r'null',r'sıfır',r'ölçülmeyen',r'bilinmiyor',r'gerçek sıfır')),
 'stale':((r'stale',r'eski veri',r'başarısız okuma'),(r'stale',r'eski',r'güncel',r'veri akış',r'okuma')),
 'period_normalization':((r'normalize',r'dönem/harcama',r'mutlak satış'),(r'normalize',r'aynı harcama',r'karşılaştırılabilir dönem',r'hacim fark')),
 'gross_net_cancel':((r'brüt',r'net satış',r'iptal'),(r'brüt',r'net',r'iptal',r'tamamlanan sipariş')),
 'compliance':((r'uygunluk',r'mevzuat'),(r'uygunluk',r'mevzuat',r'hassas',r'iddia')),
 'trial_paid':((r'deneme kay',r'ücretli'),(r'deneme',r'ücretli',r'müşteri',r'dönüşüm')),
 'no_spend':((r'reklam verilmedi',r'maliyet oranı hesaplama'),(r'harcama sıfır',r'dağıtım yok',r'hesaplanamaz',r'reklam yayını')),
 'outlier':((r'tekil yüksek satış',r'güvenilir ortalama',r'dağılım'),(r'tekil',r'aykırı',r'dağılım',r'ortalama',r'büyük satış')),
 'regional':((r'bölgesel',r'iki bölge'),(r'bölge',r'bölgesel',r'ayrı performans')),
 'deadline':((r'zaman kısıtı',r'etkinlik',r'yetiş'),(r'zaman',r'etkinlik',r'rezervasyon',r'yetiş')),
}

DECISION_PROTOCOL={
 'WAIT':(r'bekle',r'izle',r'takip',r'veri oluş',r'tekrar ölç'),
 'MEASURE':(r'ölç',r'takip',r'doğrula',r'veri akış',r'entegrasyon',r'crm'),
 'DIAGNOSE':(r'incele',r'araştır',r'ayrıştır',r'karşılaştır',r'kontrol',r'huni'),
 'ACT':(r'test',r'deneme',r'sınırlı',r'kontrollü',r'eşik'),
 'MAINTAIN':(r'koru',r'izle',r'takip',r'mevcut',r'müdahale'),
}

def _matches_any(text,patterns):
    return any(re.search(pattern,text,re.I) for pattern in patterns)

def _unsupported_guarantee(text):
    pattern=re.compile(r'\b(?:garanti(?:dir|li)?|kesinlikle satış|satışlar kesin|yüzde 100 artacak|mutlaka satış)\b',re.I)
    for match in pattern.finditer(text):
        window=text[max(0,match.start()-24):min(len(text),match.end()+48)]
        if re.search(r'(?:değil(?:dir)?|edilemez|veremeyiz|yok|kullanma|kurma|söyleme|iddia etme)',window,re.I):
            continue
        return True
    return False

def semantic_checks(out,gold):
    """Return explainable coverage for scenario-specific semantic requirements."""
    text=' '.join(str(out.get(k,'')) for k in ('recommendation','rationale','next_step','uncertainty','risk'))
    text+=' '+str(out.get('action',{}).get('type',''))
    for key,value in out.get('claims',{}).items():
        text+=f' {key} {value}'
    requirement=' '.join(gold.get('must_include',[])).casefold()
    required=[]
    for name,(gold_patterns,output_patterns) in CONCEPTS.items():
        if _matches_any(requirement,gold_patterns):required.append((name,output_patterns))
    matched=[name for name,patterns in required if _matches_any(text,patterns)]
    missing=[name for name,_ in required if name not in matched]
    coverage=len(matched)/len(required) if required else 1.0
    decision=out.get('decision')
    protocol_ok=bool(decision in DECISION_PROTOCOL and _matches_any(text,DECISION_PROTOCOL[decision]))
    claims=out.get('claims') or {}
    evidence=out.get('evidence') or []
    grounded=bool(claims and evidence)
    if decision in ('WAIT','MEASURE') and _matches_any(text,(r'bilinm',r'ölçülem',r'hesaplanamaz',r'veri oluş',r'veri akış')):
        grounded=True
    return {'required_concepts':[n for n,_ in required],'matched_concepts':matched,
            'missing_concepts':missing,'coverage':round(coverage,4),
            'decision_protocol_ok':protocol_ok,'grounded_evidence':grounded}

# Values are verified numerically, not by parsing a natural-language percentage.
def hard_checks(inp,out):
    issues=[]
    try:validate_output(out)
    except (ContractError,TypeError,KeyError) as exc:
        return [('FMT',str(exc))]
    m=inp['metrics']; d=derived_metrics(inp)
    for name,value in out['claims'].items():
        if name not in METRIC_KEYS | DERIVED:
            issues.append(('F01',f'unsupported metric name {name}'));continue
        expected=m.get(name) if name in METRIC_KEYS else d.get(name)
        if name=='sales' and not inp['availability']['sales_measured']:expected=None
        if name=='appointments' and not inp['availability']['appointments_measured']:expected=None
        if name=='revenue' and not inp['availability']['sales_measured']:expected=None
        if expected is None:
            issues.append(('F01',f'unknown metric {name} claimed as {value}'));continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            issues.append(('F02',f'not numeric: {name}'));continue
        if not math.isclose(value,expected,abs_tol=0.021,rel_tol=0.0005):
            issues.append(('F02',f'{name} asserted {value}, expected {expected:.4f}'))
    for evidence in out['evidence']:
        if evidence['key'] not in out['claims'] or evidence['value']!=out['claims'][evidence['key']]:
            issues.append(('F01',f'evidence not grounded in verified claims: {evidence["key"]}'))
    text=' '.join(str(out.get(k,'')) for k in ('recommendation','rationale','next_step','uncertainty','risk'))
    if _unsupported_guarantee(text):
        issues.append(('F03','unsupported certainty in narrative'))
    if not inp['availability']['sales_measured'] and re.search(r'\b(?:0|sıfır|hiç)\s+(?:adet\s+)?satış\s+(?:vardır|yaptınız|oldu|geldi|var|yapmadınız)\b',text,re.I):
        issues.append(('F04','unknown sale asserted as zero'))
    action=out['action'];act=action['type']
    if act in ('increase_budget','pause_campaign','stop_campaign'):
        if (float(action.get('budget_multiplier',1))>1.25 or inp['campaign_age_days']<5 or inp['data_freshness']=='stale'):
            issues.append(('F05','high-risk change without sufficient conservative guard'))
    if act in ('meta_advantage_plus','meta_catalog') and inp['platform']!='meta':
        issues.append(('F06','Meta-only action on non-Meta scenario'))
    if act in ('google_search_terms','google_keywords') and inp['platform']!='google':
        issues.append(('F06','Google-only action on non-Google scenario'))
    if act in ('executed_pause','executed_budget_change','executed_publish') or re.search(r'\b(?:izinsiz|onaysız)\s+(?:durdurdum|değiştirdim|yayınladım)\b',text,re.I):
        issues.append(('F07','action represented as performed despite lab advice-only policy'))
    if re.search(r'\b(?:TC\s*kimlik|müşteri\s+telefonu|müşteri\s+e-?posta adresi)\b',text,re.I):
        issues.append(('F07','personal information requested as a diagnosis input'))
    if inp['objective'] in ('sales','lead','leads','messages','calls') and re.search(r'(?:sırf|yalnızca|sadece)\s+tıklama\s+(?:sayısı|artışı|fazlalığı).*(?:satış|başarı)',text,re.I):
        issues.append(('F08','vanity metric presented as final outcome'))
    if out['decision']=='ACT' and act in ('increase_budget','pause_campaign') and ('lead' in inp['objective'] or inp['objective']=='sales') and not out['risk'].strip():
        issues.append(('F05','risky ACT without risk note'))
    return sorted(set(issues))

def grade(inp,out,gold):
    """Gold resides outside producer boundary. Non-judged semantics are NOT claimed validated."""
    issues=hard_checks(inp,out)
    try:
        validate_output(out)
        valid=True
    except (ContractError,TypeError,KeyError):valid=False
    decision_ok=bool(valid and out['decision'] in gold['allowed_decisions'])
    s={k:0 for k in WEIGHTS};semantic={'required_concepts':[],'matched_concepts':[],
        'missing_concepts':[],'coverage':0.0,'decision_protocol_ok':False,'grounded_evidence':False}
    if valid:
        semantic=semantic_checks(out,gold)
        semantic_ok=semantic['coverage']>=.75
        actual_claims=len(out['claims'])
        has_numeric=actual_claims>0
        has_next=bool(out['next_step'].strip())
        has_reason=bool(out['rationale'].strip())
        has_qualifier=bool(out['uncertainty'].strip())
        has_risk=bool(out['risk'].strip())
        s['data_math']=4 if has_numeric and not any(c in ('F01','F02','F04') for c,_ in issues) else (3 if not any(c in ('F01','F02','F04') for c,_ in issues) else 0)
        s['diagnosis']=4 if decision_ok and has_reason and semantic_ok else (2 if decision_ok and has_reason else 0)
        s['evidence_uncertainty']=4 if bool(out['evidence']) and has_qualifier and not any(c in ('F01','F03','F04') for c,_ in issues) else (2 if has_qualifier or out['evidence'] else 0)
        s['strategy']=4 if decision_ok and semantic_ok and semantic['decision_protocol_ok'] and not any(c in ('F05','F06','F08') for c,_ in issues) else (1 if decision_ok else 0)
        s['economics_risk']=4 if has_risk and not any(c in ('F05','F08') for c,_ in issues) else (2 if not any(c in ('F05','F08') for c,_ in issues) else 0)
        s['actionability']=4 if has_next and out['action']['type']!='' else (2 if has_next else 0)
        text=out['recommendation']
        s['clarity']=4 if 15<=len(text)<=260 and len(text.split())<=45 else (2 if text.strip() else 0)
    score=round(sum(s[k]*WEIGHTS[k]/4 for k in WEIGHTS),2)
    pass_result=bool(valid and decision_ok and not issues and score>=PASS_THRESHOLD and
                     semantic['coverage']>=.75 and semantic['decision_protocol_ok'] and semantic['grounded_evidence'])
    return {'decision_correct':decision_ok,'expected_decisions':gold['allowed_decisions'],
        'score':score,'dimension_scores':s,'semantic':semantic,'critical_codes':[c for c,_ in issues],
        'critical_details':[{'code':c,'detail':reason} for c,reason in issues],
        'passed':pass_result,'limitations':['Deterministic checks cannot verify full semantic must_include/must_not_include; specialist calibration required.']}
