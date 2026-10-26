"""Input/output contracts; Python standard library only.

DATA LEAK BARRIER: generate_input strips identifiers and all gold/expectation fields.
"""
from __future__ import annotations
import copy, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DECISIONS={"ACT", "WAIT", "DIAGNOSE", "MEASURE", "MAINTAIN"}
WEIGHTS={"data_math":20, "diagnosis":20, "evidence_uncertainty":15,
         "strategy":15, "economics_risk":15, "actionability":10, "clarity":5}
METRIC_KEYS={"spend", "impressions", "clicks", "leads", "appointments", "sales", "revenue", "target_cost_per_result"}
DERIVED={"cpc", "cpl", "cpa_appointment", "cpa_sale", "ctr_pct", "roas"}

class ContractError(ValueError):
    pass

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return float(n)/float(d)

def derived_metrics(data):
    m=data["metrics"]
    sales = m.get("sales") if data["availability"]["sales_measured"] else None
    appts = m.get("appointments") if data["availability"]["appointments_measured"] else None
    revenue=m.get("revenue") if sales is not None else None
    return {
        "cpc":safe_div(m.get("spend"),m.get("clicks")),
        "cpl":safe_div(m.get("spend"),m.get("leads")),
        "cpa_appointment":safe_div(m.get("spend"),appts),
        "cpa_sale":safe_div(m.get("spend"),sales),
        "ctr_pct":None if safe_div(m.get("clicks"),m.get("impressions")) is None else 100*safe_div(m.get("clicks"),m.get("impressions")),
        "roas":safe_div(revenue,m.get("spend")),
    }

def validate_input(data):
    if not isinstance(data,dict):raise ContractError('input not an object')
    req=['sector','platform','objective','campaign_age_days','observation_window_days','currency','metrics','availability','data_freshness','context','synthetic']
    for k in req:
        if k not in data:raise ContractError(f'missing required {k}')
    if data['synthetic'] is not True:raise ContractError('only synthetic scenarios allowed')
    if data['platform'] not in ('meta','google'):raise ContractError('only explicit scenario platform meta/google allowed in v1')
    if not isinstance(data['sector'],str) or not data['sector'].strip():raise ContractError('missing sector')
    if not isinstance(data['context'],str):raise ContractError('invalid context')
    if data['currency']!='TRY':raise ContractError('v1 scenario currency expects TRY; add currency adapter otherwise')
    for k in ['campaign_age_days','observation_window_days']:
        x=data[k]
        if not isinstance(x,int) or isinstance(x,bool) or x<0:raise ContractError(f'invalid {k}')
    if data['data_freshness'] not in ('current','stale'):raise ContractError('data freshness enum invalid')
    a=data['availability'];m=data['metrics']
    if not isinstance(a,dict) or not isinstance(m,dict):raise ContractError('invalid metrics/availability')
    for k in ('sales_measured','appointments_measured'):
        if not isinstance(a.get(k),bool):raise ContractError(f'{k} missing bool')
    for k in m:
        if k not in METRIC_KEYS:raise ContractError(f'unknown metric {k}')
        v=m[k]
        if v is None:continue
        if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0:raise ContractError(f'invalid metric {k}')
        if k in ('impressions','clicks','leads','appointments','sales') and int(v)!=v:raise ContractError(f'{k} must be count')
    for k in ('spend','clicks','impressions'):
        if k not in m or m[k] is None:raise ContractError(f'{k} required')
    if m['clicks']>m['impressions']:raise ContractError('clicks cannot exceed impressions in this test contract')
    for metric,flag in [('sales','sales_measured'),('appointments','appointments_measured')]:
        if not a[flag] and m.get(metric) is not None:raise ContractError(f'{metric} measured=false but metric nonnull')
        if a[flag] and m.get(metric) is None:raise ContractError(f'{metric} measured=true but value missing')
    if m.get('revenue') is not None and not a['sales_measured']:raise ContractError('revenue needs measured sales in this fixture')
    return True

def validate_expectation(e):
    if not isinstance(e,dict):raise ContractError('expectation invalid')
    decisions=e.get('allowed_decisions')
    if not isinstance(decisions,list) or not decisions or not set(decisions)<=DECISIONS:raise ContractError('allowed_decisions invalid')
    for key in ['must_include','must_not_include']:
        value=e.get(key)
        if not isinstance(value,list) or not value or not all(isinstance(x,str) and x.strip() for x in value):
            raise ContractError(f'expectation {key} needs non-empty strings')
    if not isinstance(e.get('reference_rationale'),str) or not e['reference_rationale'].strip():
        raise ContractError('expectation reference_rationale needs text')
    fails=e.get('critical_fails')
    if not isinstance(fails,list) or not set(fails)<={f'F{i:02d}' for i in range(1,9)}:
        raise ContractError('expectation critical_fails invalid')
    return True

def generate_input(record):
    """Strict capability boundary: producer never sees id, group, gold or expectation."""
    data=copy.deepcopy(record['input'])
    validate_input(data)
    data.pop('scenario_id',None)
    data.pop('id',None)
    return data

def validate_output(result):
    if not isinstance(result,dict):raise ContractError('output must be JSON object')
    if result.get('decision') not in DECISIONS:raise ContractError('decision invalid')
    for key in ('recommendation','rationale','next_step','uncertainty','risk'):
        if not isinstance(result.get(key),str):raise ContractError(f'{key} required string')
    if not isinstance(result.get('evidence'),list):raise ContractError('evidence must be list')
    for item in result['evidence']:
        if not isinstance(item,dict) or not isinstance(item.get('key'),str) or not isinstance(item.get('value'),(int,float,str)):
            raise ContractError('evidence item needs key and value')
    if not isinstance(result.get('claims'),dict):raise ContractError('claims must be a dictionary')
    a=result.get('action')
    if not isinstance(a,dict) or not isinstance(a.get('type'),str):raise ContractError('action must specify type')
    if 'budget_multiplier' in a and (not isinstance(a['budget_multiplier'],(int,float)) or not math.isfinite(a['budget_multiplier'])):raise ContractError('invalid multiplier')
    return True

def normalized_number(num):
    return round(num,2) if isinstance(num,(int,float)) else num
