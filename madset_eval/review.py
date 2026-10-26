"""Independent dual-expert human review: exported blank forms and agreement analysis."""
from __future__ import annotations
import csv,json
from collections import Counter
from pathlib import Path
from .contracts import WEIGHTS

FIELDS=['run_id','scenario_id','trial','reviewer_id','scenario_json','decision','recommendation','rationale',
        'next_step','uncertainty','risk','correct_decision','critical_error_codes','data_math','diagnosis',
        'evidence_uncertainty','strategy','economics_risk','actionability','clarity','overall_pass','notes',
        'automatic_pass']

def export_template(path_run,path_out):
    data=json.loads(Path(path_run).read_text(encoding='utf-8'))
    with open(path_out,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for r in data['results']:
            for reviewer in ['expert_1','expert_2']:
                out=r.get('output',{})
                w.writerow({'run_id':data['metadata']['run_id'],'scenario_id':r['scenario_id'],
                            'trial':r['trial'],'reviewer_id':reviewer,
                            'scenario_json':json.dumps(r.get('input',{}),ensure_ascii=False,sort_keys=True),
                            'decision':out.get('decision',''),'recommendation':out.get('recommendation',''),
                            'rationale':out.get('rationale',''),'next_step':out.get('next_step',''),
                            'uncertainty':out.get('uncertainty',''),'risk':out.get('risk',''),
                            'correct_decision':'','critical_error_codes':'','overall_pass':'','notes':'',
                            # Kept as the final column so it can be hidden before assigning reviewers.
                            'automatic_pass':r.get('grade',{}).get('passed','')})
    return str(path_out)

def analyze_review(path_csv):
    pairs={};automatic={}
    with open(path_csv,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r['overall_pass'].lower() not in ('true','false','1','0','yes','no'):continue
            key=(r['scenario_id'],r['trial'])
            if key not in pairs:pairs[key]={}
            x=r['overall_pass'].lower() in ('true','1','yes')
            pairs[key][r['reviewer_id']]=x
            if r.get('automatic_pass','').lower() in ('true','false','1','0','yes','no'):
                automatic[key]=r['automatic_pass'].lower() in ('true','1','yes')
    valid=[(key,review['expert_1'],review['expert_2']) for key,review in pairs.items()
           if 'expert_1' in review and 'expert_2' in review]
    if not valid:return {'annotated_pairs':0,'status':'NO_EXPERT_LABELS','cohens_kappa':None,'agreement':None}
    n=len(valid);agree=sum(a==b for _,a,b in valid)/n
    yes_1=sum(a for _,a,b in valid)/n;yes_2=sum(b for _,a,b in valid)/n
    pe=yes_1*yes_2+(1-yes_1)*(1-yes_2)
    kappa=(agree-pe)/(1-pe) if pe<1 else (1.0 if agree==1 else None)
    consensus={key:a for key,a,b in valid if a==b}
    compared=[(automatic[key],human) for key,human in consensus.items() if key in automatic]
    tp=sum(auto and human for auto,human in compared);tn=sum(not auto and not human for auto,human in compared)
    fp=sum(auto and not human for auto,human in compared);fn=sum(not auto and human for auto,human in compared)
    return {'annotated_pairs':n,'status':'REVIEW_DATA_PRESENT',
            'agreement':round(agree,4),'cohens_kappa':round(kappa,4) if kappa is not None else None,
            'disputed':sum(a!=b for _,a,b in valid),'consensus_pairs':len(consensus),
            'grader_vs_consensus':{'n':len(compared),'true_positive':tp,'true_negative':tn,
              'false_positive':fp,'false_negative':fn,
              'recall':round(tp/(tp+fn),4) if tp+fn else None,
              'false_positive_rate':round(fp/(fp+tn),4) if fp+tn else None,
              'agreement':round((tp+tn)/len(compared),4) if compared else None},
            'caution':'Disputed pairs require adjudication before final grader calibration.'}
