"""Isolated offline runner, reports, version comparison."""
from __future__ import annotations
from datetime import datetime,timezone
import csv,hashlib,importlib,json,time,statistics,uuid,copy
from pathlib import Path
from .contracts import ROOT,generate_input,validate_expectation,load_json,validate_input
from .grading import grade,hard_checks
from .judging import merge_judgment
from .baselines import BASELINES

VERSIONS={'v1':('rule-baseline-1','rules-v1'), 'v2':('rule-baseline-2','rules-v2'), 'v3':('rule-baseline-3','rules-v3')}

def manifest_hash(path):
    """Hash text consistently across LF and CRLF Git checkouts."""
    content=Path(path).read_bytes().replace(b'\r\n',b'\n')
    return hashlib.sha256(content).hexdigest()

def load_split(split):
    if split=='dev': return load_json(ROOT/'data/dev/scenarios.json')
    if split=='holdout':return load_json(ROOT/'data/holdout/inputs.json')
    if split=='holdout_v2':return load_json(ROOT/'data/holdout_v2/inputs.json')
    raise ValueError('split must be dev, holdout or holdout_v2')

def gold_for(split,records):
    if split=='dev':return {i['id']:i['expectation'] for i in records}
    # Loaded only in isolated scoring stage, NEVER handed to the model/adapters.
    source=load_json(ROOT/('data/holdout/private/gold.json' if split=='holdout' else 'data/holdout_v2/private/gold.json'))
    return {i['id']:i['expectation'] for i in source}

def validate_suite():
    dev=load_split('dev');hold=load_split('holdout');hold2=load_split('holdout_v2')
    all_ids=set();errors=[]
    for split, records in (('dev',dev),('holdout',hold),('holdout_v2',hold2)):
        for record in records:
            if record['id'] in all_ids:errors.append(f'duplicate {record["id"]}')
            all_ids.add(record['id'])
            try:validate_input(record['input'])
            except Exception as ex:errors.append(f'{record["id"]} input: {ex}')
            if record['input'].get('scenario_id')!=record['id']:errors.append(f'{record["id"]}: id mismatch')
            if split.startswith('holdout') and 'expectation' in record:errors.append(f'{record["id"]}: expectation leaked into holdout input')
            if split=='dev':
                try:validate_expectation(record['expectation'])
                except Exception as ex:errors.append(f'{record["id"]} expectation: {ex}')
    hgold=gold_for('holdout',hold)
    if set(hgold)!={x['id'] for x in hold}:errors.append('holdout gold IDs do not match input IDs')
    for id, e in hgold.items():
        try:validate_expectation(e)
        except Exception as ex:errors.append(f'{id} holdout expectation: {ex}')
    hgold2=gold_for('holdout_v2',hold2)
    if set(hgold2)!={x['id'] for x in hold2}:errors.append('holdout_v2 gold IDs do not match input IDs')
    for id,e in hgold2.items():
        try:validate_expectation(e)
        except Exception as ex:errors.append(f'{id} holdout_v2 expectation: {ex}')
    if len(dev)<30 or len(hold)<10 or len(hold)/(len(dev)+len(hold))<.25:errors.append('sample counts insufficient')
    manifest=load_json(ROOT/'data/manifest.json')
    for relative,expected_hash in manifest.get('files',{}).items():
        path=ROOT/relative
        if not path.exists():errors.append(f'manifest file missing: {relative}');continue
        actual=manifest_hash(path)
        if actual!=expected_hash:errors.append(f'manifest hash mismatch: {relative}')
    return {'valid':not errors,'errors':errors,'dev':len(dev),'holdout':len(hold),
            'holdout_v2':len(hold2),'total':len(dev)+len(hold),'total_original':len(dev)+len(hold),'total_with_new_holdout':len(all_ids),
            'holdout_rate':round(len(hold)/(len(dev)+len(hold)),4)}

def choose_producer(model,adapter=None):
    if model in BASELINES:return BASELINES[model]
    if model!='external':raise ValueError('model must be v1/v2/v3/external')
    if not adapter or ':' not in adapter:raise ValueError('external requires --adapter module:function')
    module,name=adapter.rsplit(':',1)
    func=getattr(importlib.import_module(module),name)
    if not callable(func):raise ValueError('adapter is not callable')
    return func

def load_adapter(adapter):
    if not adapter or ':' not in adapter:raise ValueError('adapter must be module:function')
    module,name=adapter.rsplit(':',1)
    func=getattr(importlib.import_module(module),name)
    if not callable(func):raise ValueError('adapter is not callable')
    return func

def exec_run(model='v3',split='dev',trials=1,adapter=None,folder=None,save=True,judge_adapter=None):
    if not isinstance(trials,int) or trials<1 or trials>20:raise ValueError('trials must be 1..20')
    v=validate_suite()
    if not v['valid']:raise ValueError('invalid suite: '+str(v['errors']))
    producer=choose_producer(model,adapter)
    judge_func=load_adapter(judge_adapter) if judge_adapter else None
    records=load_split(split)
    started=datetime.now(timezone.utc).isoformat()
    run_id=uuid.uuid4().hex[:12]
    generated=[]
    # Producer runs with redacted input before evaluator opens gold keys.
    for item in records:
        for number in range(1,trials+1):
            producer_input=generate_input(item)
            begin=time.perf_counter_ns();error=None
            adapter_meta={}
            try:
                output=producer(copy.deepcopy(producer_input))
                if not isinstance(output,dict):raise ValueError('adapter output not a dict')
                output=copy.deepcopy(output)
                adapter_meta=output.pop('_eval_metadata',{}) or {}
                if not isinstance(adapter_meta,dict):raise ValueError('_eval_metadata must be an object')
                json.dumps(output,allow_nan=False)
            except Exception as e:
                error=f'{type(e).__name__}: {e}';output={'decision':None}
            elapsed=round((time.perf_counter_ns()-begin)/1e6,3)
            generated.append({'scenario_id':item['id'],'trial':number,'input':producer_input,'output':output,
                 'producer_error':error,'latency_ms':elapsed,
                 'input_tokens':adapter_meta.get('input_tokens'),
                 'output_tokens':adapter_meta.get('output_tokens'),
                 'cost_usd':0.0 if model!='external' else adapter_meta.get('cost_usd'),
                 'adapter_metadata':adapter_meta})
    expected=gold_for(split,records)
    scored=[]
    judge_usage=[]
    for g in generated:
        gold=expected[g['scenario_id']]
        gs=grade(g['input'],g['output'],gold)
        judge_error=None;judge_latency_ms=None;judge_meta={}
        if judge_func and not g['producer_error']:
            begin=time.perf_counter_ns()
            try:
                judgment=judge_func({'input':copy.deepcopy(g['input']),'output':copy.deepcopy(g['output']),'expectation':copy.deepcopy(gold)})
                if not isinstance(judgment,dict):raise ValueError('judge adapter output not a dict')
                judgment=copy.deepcopy(judgment);judge_meta=judgment.pop('_eval_metadata',{}) or {}
                if not isinstance(judge_meta,dict):raise ValueError('judge _eval_metadata must be an object')
                gs=merge_judgment(gs,judgment)
            except Exception as exc:
                judge_error=f'{type(exc).__name__}: {exc}';gs=dict(gs);gs['passed']=False;gs['judge_error']=judge_error
            judge_latency_ms=round((time.perf_counter_ns()-begin)/1e6,3)
            judge_usage.append(judge_meta)
        # Synthetic input is retained as the trial transcript for audit/review.
        # Gold expectations remain outside this record.
        scored.append(g|{'grade':gs,'judge_error':judge_error,'judge_latency_ms':judge_latency_ms})
    adapter_values=lambda key:{x['adapter_metadata'].get(key) for x in generated if x['adapter_metadata'].get(key) is not None}
    adapter_identifier=adapter_values('model_identifier');adapter_version=adapter_values('model_version');adapter_prompt=adapter_values('prompt_version')
    known_costs=[x['cost_usd'] for x in generated if isinstance(x['cost_usd'],(int,float))]
    metadata={'run_id':run_id,'created_utc':started,'model':model,
        'model_identifier':VERSIONS.get(model,(next(iter(adapter_identifier),'external/unknown'),'external'))[0],
        'model_version':VERSIONS.get(model,(next(iter(adapter_version),'external/unknown'),'external'))[0],
        'rules_version':VERSIONS.get(model,('external','external'))[1],
        'grader_version':'offline-semantic-1.1','rubric_version':'1.1-provisional','prompt_version':'none-offline' if model!='external' else 'adapter-owned',
        'split':split,'trials_per_case':trials,'scenario_version':'1.0','adapter':adapter,
        'estimated_cost_usd':0 if model!='external' else (round(sum(known_costs),8) if len(known_costs)==len(generated) else None),
        'adapter_prompt_versions':sorted(adapter_prompt),'input_tokens':sum(x['input_tokens'] for x in generated if isinstance(x['input_tokens'],int)) or None,
        'output_tokens':sum(x['output_tokens'] for x in generated if isinstance(x['output_tokens'],int)) or None,
        'evaluation_mode':'deterministic+semantic-heuristic (not expert-certified)',
        'holdout_policy':'scoring only; do not tune candidates from holdout feedback'}
    if judge_adapter:
        judge_costs=[x.get('cost_usd') for x in judge_usage if isinstance(x.get('cost_usd'),(int,float))]
        metadata.update({'judge_adapter':judge_adapter,
            'judge_model_identifiers':sorted({x.get('model_identifier') for x in judge_usage if x.get('model_identifier')}),
            'judge_prompt_versions':sorted({x.get('prompt_version') for x in judge_usage if x.get('prompt_version')}),
            'judge_input_tokens':sum(x.get('input_tokens',0) for x in judge_usage if isinstance(x.get('input_tokens'),int)) or None,
            'judge_output_tokens':sum(x.get('output_tokens',0) for x in judge_usage if isinstance(x.get('output_tokens'),int)) or None,
            'estimated_judge_cost_usd':round(sum(judge_costs),8) if len(judge_costs)==len(scored) else None,
            'evaluation_mode':'deterministic-hard-checks+external-semantic-judge (human calibration pending)'})
    response={'metadata':metadata,'results':scored,'summary':summarize(scored)}
    if folder and save:
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
        out=folder/f'{model}_{split}_{run_id}.json';out.write_text(json.dumps(response,ensure_ascii=False,indent=2),encoding='utf-8')
        export_csv(response,folder/f'{model}_{split}_{run_id}.csv')
        response['file_path']=str(out)
    return response

def regrade_run(path,folder=None,judge_adapter=None,limit=None,progress=False,unique_scenarios=False,resume=False):
    """Re-score a saved transcript without calling its producer again."""
    source=Path(path);run=json.loads(source.read_text(encoding='utf-8'))
    split=run['metadata']['split'];records=load_split(split);expected=gold_for(split,records)
    rows=run['results']
    if unique_scenarios:
        seen=set();rows=[row for row in rows if not (row['scenario_id'] in seen or seen.add(row['scenario_id']))]
    if limit is not None and (not isinstance(limit,int) or limit<1):raise ValueError('limit must be a positive integer')
    rescored=[];judge_func=load_adapter(judge_adapter) if judge_adapter else None;judge_usage=[]
    destination=Path(folder) if folder else None
    if destination:destination.mkdir(parents=True,exist_ok=True)
    partial_path=destination/(source.stem+'_judging_partial.json') if destination and judge_adapter else None
    if resume and partial_path and partial_path.exists():
        previous=json.loads(partial_path.read_text(encoding='utf-8'))
        rescored=[row for row in previous.get('results',[]) if not row.get('judge_error') and row.get('grade',{}).get('judge')]
        judge_usage=[row.get('judge_metadata',{}) for row in rescored if isinstance(row.get('judge_metadata'),dict)]
        completed={(row['scenario_id'],row.get('trial')) for row in rescored}
        rows=[row for row in rows if (row['scenario_id'],row.get('trial')) not in completed]
    target_total=limit if limit is not None else len(rescored)+len(rows)
    remaining=max(0,target_total-len(rescored))
    rows=rows[:remaining]
    for row in rows:
        index=len(rescored)+1
        if 'input' not in row:raise ValueError('saved run has no input transcript; cannot regrade safely')
        if progress:print(f'[{index}/{target_total}] {row["scenario_id"]}: Claude değerlendirmesi başlıyor...',flush=True)
        updated=copy.deepcopy(row);gold=expected[updated['scenario_id']]
        updated['grade']=grade(updated['input'],updated['output'],gold)
        updated['judge_error']=None;updated['judge_latency_ms']=None
        if judge_func and not updated.get('producer_error'):
            begin=time.perf_counter_ns()
            try:
                judgment=judge_func({'input':copy.deepcopy(updated['input']),'output':copy.deepcopy(updated['output']),'expectation':copy.deepcopy(gold)})
                judgment=copy.deepcopy(judgment);meta=judgment.pop('_eval_metadata',{}) or {};judge_usage.append(meta)
                updated['grade']=merge_judgment(updated['grade'],judgment)
                updated['judge_metadata']=meta
            except Exception as exc:
                updated['judge_error']=f'{type(exc).__name__}: {exc}';updated['grade']['passed']=False;updated['grade']['judge_error']=updated['judge_error']
            updated['judge_latency_ms']=round((time.perf_counter_ns()-begin)/1e6,3)
        rescored.append(updated)
        if progress:
            status='HATA: '+updated['judge_error'] if updated.get('judge_error') else 'tamamlandı'
            print(f'[{index}/{target_total}] {row["scenario_id"]}: {status}',flush=True)
        if partial_path:
            checkpoint={'metadata':copy.deepcopy(run['metadata']),'results':rescored,'summary':summarize(rescored)}
            checkpoint['metadata'].update({'judge_adapter':judge_adapter,'status':'partial','completed_judge_calls':len(rescored)})
            partial_path.write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2),encoding='utf-8')
        if updated.get('judge_error'):
            break
    result={'metadata':copy.deepcopy(run['metadata']),'results':rescored,'summary':summarize(rescored)}
    result['metadata']['regraded_from_run_id']=run['metadata']['run_id']
    result['metadata']['grader_version']='offline-semantic-1.1'
    result['metadata']['rubric_version']='1.1-provisional'
    result['metadata']['regraded_utc']=datetime.now(timezone.utc).isoformat()
    if judge_adapter:
        judge_costs=[x.get('cost_usd') for x in judge_usage if isinstance(x.get('cost_usd'),(int,float))]
        result['metadata']['judge_adapter']=judge_adapter
        result['metadata']['judge_model_identifiers']=sorted({x.get('model_identifier') for x in judge_usage if x.get('model_identifier')})
        result['metadata']['judge_prompt_versions']=sorted({x.get('prompt_version') for x in judge_usage if x.get('prompt_version')})
        result['metadata']['judge_input_tokens']=sum(x.get('input_tokens',0) for x in judge_usage if isinstance(x.get('input_tokens'),int)) or None
        result['metadata']['judge_output_tokens']=sum(x.get('output_tokens',0) for x in judge_usage if isinstance(x.get('output_tokens'),int)) or None
        result['metadata']['estimated_judge_cost_usd']=round(sum(judge_costs),8) if len(judge_costs)==len(rescored) else None
        result['metadata']['evaluation_mode']='deterministic-hard-checks+external-semantic-judge (human calibration pending)'
    if folder:
        out=destination/(source.stem+'_regraded.json')
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        export_csv(result,out.with_suffix('.csv'));result['file_path']=str(out)
    return result

def summarize(records):
    n=len(records);passes=sum(x['grade']['passed'] for x in records)
    ok=sum(x['grade']['decision_correct'] for x in records)
    failures=sum(bool(x['grade']['critical_codes']) for x in records)
    by_case={sid:[r['grade']['passed'] for r in records if r['scenario_id']==sid] for sid in {x['scenario_id'] for x in records}}
    # Observed pass@k = fraction of cases with >=1 success across the supplied trials.
    # Observed pass^k = fraction of cases whose ALL trials passed. Neither is a population probability estimate.
    judge_latencies=[x.get('judge_latency_ms') for x in records if isinstance(x.get('judge_latency_ms'),(int,float))]
    return {'trials':n,'passed':passes,'pass_rate':round(passes/n,4) if n else None,
       'decision_accuracy':round(ok/n,4) if n else None,'critical_failure_rate':round(failures/n,4) if n else None,
       'avg_score':round(statistics.mean(x['grade']['score'] for x in records),2) if n else None,
       'median_score':round(statistics.median(x['grade']['score'] for x in records),2) if n else None,
       'avg_latency_ms':round(statistics.mean(x['latency_ms'] for x in records),3) if n else None,
       'avg_judge_latency_ms':round(statistics.mean(judge_latencies),3) if judge_latencies else None,
       'observed_pass_at_k':round(sum(any(vals) for vals in by_case.values())/len(by_case),4) if n else None,
       'observed_pass_pow_k':round(sum(all(vals) for vals in by_case.values())/len(by_case),4) if n else None,
       'scenario_pass_all_trials':round(sum(all(vals) for vals in by_case.values())/len(by_case),4) if n else None,
       'error_code_counts':{c:sum(c in r['grade']['critical_codes'] for r in records) for c in ('F01','F02','F03','F04','F05','F06','F07','F08','FMT')}}

def export_csv(response,path):
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['run_id','model','split','scenario_id','trial','decision','accepted','score','pass','critical_codes','latency_ms','recommendation'])
        w.writeheader();meta=response['metadata']
        for r in response['results']:
            g=r['grade'];out=r['output']
            w.writerow({'run_id':meta['run_id'],'model':meta['model'],'split':meta['split'],'scenario_id':r['scenario_id'],
                        'trial':r['trial'],'decision':out.get('decision'),'accepted':'/'.join(g['expected_decisions']),
                        'score':g['score'],'pass':g['passed'],'critical_codes':','.join(g['critical_codes']),
                        'latency_ms':r['latency_ms'],'recommendation':out.get('recommendation','')})

def compare(a,b):
    if a['metadata']['split']!=b['metadata']['split']:raise ValueError('cannot compare different splits')
    if a['metadata']['scenario_version']!=b['metadata']['scenario_version']:raise ValueError('scenario versions differ')
    def rates(run):
        grouped={}
        for row in run['results']:grouped.setdefault(row['scenario_id'],[]).append(bool(row['grade']['passed']))
        return {sid:sum(vals)/len(vals) for sid,vals in grouped.items()}
    ag=rates(a);bg=rates(b)
    if set(ag)!=set(bg):raise ValueError('mismatched scenario IDs')
    regress=[x for x in sorted(ag) if bg[x]<ag[x]]
    gains=[x for x in sorted(ag) if bg[x]>ag[x]]
    deltas=[{'scenario_id':x,'from_pass_rate':round(ag[x],4),'to_pass_rate':round(bg[x],4),
             'delta':round(bg[x]-ag[x],4)} for x in sorted(ag)]
    return {'split':a['metadata']['split'],'from':a['metadata']['model'],'to':b['metadata']['model'],
            'from_pass':a['summary']['pass_rate'],'to_pass':b['summary']['pass_rate'],
            'pass_delta':round(b['summary']['pass_rate']-a['summary']['pass_rate'],4),
            'from_avg_score':a['summary']['avg_score'],'to_avg_score':b['summary']['avg_score'],
            'regressions':regress,'improvements':gains,'scenario_deltas':deltas,
            'note':'Paired comparison uses each scenario\'s pass rate across all supplied trials.'}
