"""CLI: python -m madset_eval ..."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .runs import validate_suite,exec_run,compare,regrade_run
from .calibration import measure
from .reporting import render_dashboard,render_report
from .review import export_template,analyze_review

def main(argv=None):
    p=argparse.ArgumentParser(description='Madset standalone synthetic eval lab. Standard library only.')
    sp=p.add_subparsers(dest='command',required=True)
    sp.add_parser('validate',help='Validate all 40 synthetic scenarios and holdout separation')
    run=sp.add_parser('run',help='Run and grade a baseline or an external adapter')
    run.add_argument('--model',choices=['v1','v2','v3','external'],default='v3')
    run.add_argument('--split',choices=['dev','holdout','holdout_v2'],default='dev')
    run.add_argument('--trials',type=int,default=1)
    run.add_argument('--adapter',help='For --model external: python module:function')
    run.add_argument('--judge-adapter',help='Optional semantic judge: python module:function')
    run.add_argument('--out',default='outputs/runs')
    comp=sp.add_parser('compare',help='Compare two saved run JSONs')
    comp.add_argument('old');comp.add_argument('new');comp.add_argument('--out',default=None)
    regrade=sp.add_parser('regrade',help='Re-score a saved transcript without rerunning its producer')
    regrade.add_argument('run_json');regrade.add_argument('--out',default='outputs/regraded')
    regrade.add_argument('--judge-adapter',help='Optional semantic judge: python module:function')
    regrade.add_argument('--limit',type=int,default=None,help='Maximum records to regrade')
    regrade.add_argument('--progress',action='store_true',help='Print progress for every record')
    regrade.add_argument('--unique-scenarios',action='store_true',help='Use only the first trial of each scenario')
    regrade.add_argument('--resume',action='store_true',help='Resume successful records from an existing partial file')
    mut=sp.add_parser('calibrate',help='Run positive and negative mutation controls')
    mut.add_argument('--out',default=None)
    rev=sp.add_parser('review-export',help='Create blank forms for two independent expert graders')
    rev.add_argument('run_json');rev.add_argument('--out',default='outputs/review_template.csv')
    rev2=sp.add_parser('review-analyze',help='Analyze two expert pass/fail labels')
    rev2.add_argument('review_csv')
    demo=sp.add_parser('demo',help='Run three measured offline versions and generate a final report')
    demo.add_argument('--out',default='outputs/demo');demo.add_argument('--trials',type=int,default=3)
    args=p.parse_args(argv)
    if args.command=='validate':
        output=validate_suite();print(json.dumps(output,ensure_ascii=False,indent=2));return 0 if output['valid'] else 1
    if args.command=='run':
        output=exec_run(args.model,args.split,args.trials,args.adapter,folder=args.out,judge_adapter=args.judge_adapter)
        print(json.dumps({'file':output.get('file_path'),'summary':output['summary'],'metadata':output['metadata']},ensure_ascii=False,indent=2));return 0
    if args.command=='compare':
        a=json.loads(Path(args.old).read_text(encoding='utf-8'));b=json.loads(Path(args.new).read_text(encoding='utf-8'))
        result=compare(a,b)
        if args.out:Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    if args.command=='regrade':
        output=regrade_run(args.run_json,args.out,args.judge_adapter,args.limit,args.progress,args.unique_scenarios,args.resume)
        print(json.dumps({'file':output.get('file_path'),'summary':output['summary'],'metadata':output['metadata']},ensure_ascii=False,indent=2));return 0
    if args.command=='calibrate':
        result=measure();txt=json.dumps(result,ensure_ascii=False,indent=2)
        if args.out:Path(args.out).write_text(txt,encoding='utf-8')
        print(txt);return 0
    if args.command=='review-export':
        dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
        print(export_template(args.run_json,dest));return 0
    if args.command=='review-analyze':
        print(json.dumps(analyze_review(args.review_csv),ensure_ascii=False,indent=2));return 0
    if args.command=='demo':
        folder=Path(args.out);folder.mkdir(parents=True,exist_ok=True)
        runs={}
        for split in ('dev','holdout'):
            runs[split]={}
            for version in ('v1','v2','v3'):
                resp=exec_run(version,split,args.trials,folder=folder/'runs')
                runs[split][version]=resp
                s=resp['summary']
                print(f'{split} {version}: {s["passed"]}/{s["trials"]} passed; decision accuracy {s["decision_accuracy"]:.1%}; score {s["avg_score"]}')
        calibration=measure()
        comps=[]
        for split in ('dev','holdout'):
            for before,after in (('v1','v2'),('v2','v3'),('v1','v3')):
                comps.append(compare(runs[split][before],runs[split][after]))
        summary={'summaries':{split:{ver:runs[split][ver]['summary'] for ver in runs[split]} for split in runs},'comparisons':comps,'calibration':calibration}
        (folder/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        render_report(runs,calibration,comps,folder/'FINAL_REPORT.md')
        render_dashboard(runs,calibration,comps,folder/'DASHBOARD.html')
        print('Complete:',folder/'FINAL_REPORT.md',folder/'DASHBOARD.html');return 0
    return 1

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,FileNotFoundError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);sys.exit(2)
