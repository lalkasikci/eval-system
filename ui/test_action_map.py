"""Offline static safety checks. Run: python test_action_map.py"""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
cat=json.loads((root/'action_catalog.json').read_text(encoding='utf-8'))['actions']
assert len(cat)==12
expected={
'raise_budget_10':{'winner_underfunded','scaling_ready'},
'rewrite_greeting':{'low_messaging_rate'},
'winning_creative_variants':{'outcome_winner','schedule_completed'},
'new_creative':{'creative_fatigue','all_ads_underperforming','spend_without_outcomes','weak_ctr','ad_rejected_or_restricted'},
'mark_inbox_outcomes':{'unmarked_leads'},
'show_control_panel':{'not_delivering'},
'connect_meta_pixel':{'tracking_missing'},
'analyze_landing_page':{'click_to_landing_dropoff'},
'follow_up':{'cpa_rising','data_gap','data_stale','winner_promising'},
'info_only':{'insufficient_data','learning_phase_active','healthy_no_action','in_review_or_preparing','creative_test_starved','greeting_measuring','greeting_improved'},
'pause_ad':set(),
'restart_ad':set(),
}
actual={a['id']:set(a['findings']) for a in cat}
assert actual==expected,(actual,expected)
assert len(set.union(*actual.values()))==25
assert sum(len(x) for x in actual.values())==25
assert next(x for x in cat if x['id']=='raise_budget_10')['fallback']=={'winner_underfunded':'/control-panel','scaling_ready':'/publish'}
assert next(x for x in cat if x['id']=='rewrite_greeting')['route']=='/ads/<grup>?greeting=regen'
assert next(x for x in cat if x['id']=='winning_creative_variants')['route']=='/publish/campaign?creative=<kreatif>'
assert all(a['type']=='info' for a in cat if a['id']=='info_only')
assert all(a['approval'] and a['readback'] for a in cat if a['type']=='write')
html=(root/'index.html').read_text(encoding='utf-8')
assert html.count('data-view="rubric"')==2
assert html.count('data-view="workflow"')==2
assert html.count('data-view="scenarios"')==2
assert 'function renderRubric()' in html
assert 'function renderWorkflow()' in html
assert 'function renderScenarios()' in html
assert 'madset_ui_rubric' in html
assert 'Ağırlıkların toplamı %100 olmalı' in html
assert "fetch('/api/rubric'" in html
assert "fetch('/api/eval-results'" in html
assert "fetch('/api/scenarios/dev'" in html
assert 'Dosyalara kaydet' in html
assert "['F01','Uydurma veri'" in html
assert "['F08','Ticari hedefle çelişme'" in html
assert "['FMT','Biçim/sözleşme hatası'" in html
print('OK: aksiyon haritası, güvenlik kapıları, Rubrik ve Workflow arayüzleri doğrulandı.')
