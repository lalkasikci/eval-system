import unittest,tempfile,json,copy
from pathlib import Path
from madset_eval.runs import exec_run,compare,validate_suite,regrade_run,reprice_claude_run,analyze_judge_reliability
from madset_eval.review import export_template,analyze_review
from madset_eval.contracts import WEIGHTS

def fake_judge(payload):
 return {'decision_correct':True,'overall_pass':True,
         'dimension_scores':{key:4 for key in WEIGHTS},
         'explanation':'mock semantic approval','violations':[],
         '_eval_metadata':{'model_identifier':'mock/judge','prompt_version':'test-v1',
                           'input_tokens':10,'output_tokens':5,'cost_usd':0.001}}

class RunnerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=exec_run('v1','dev',trials=2,save=False)
  cls.b=exec_run('v3','dev',trials=2,save=False)
 def test_run_isolated_and_scored(self):
  self.assertEqual(len(self.a['results']),60)
  self.assertEqual(self.a['metadata']['estimated_cost_usd'],0)
  self.assertIn('observed_pass_pow_k',self.a['summary'])
 def test_repeat_consistency(self):
  self.assertEqual(self.b['summary']['observed_pass_pow_k'],1.0)
 def test_comparison(self):
  c=compare(self.a,self.b)
  self.assertGreater(c['pass_delta'],0)
 def test_comparison_split_guard(self):
  c=exec_run('v3','holdout',save=False)
  with self.assertRaises(ValueError):compare(self.a,c)
 def test_comparison_uses_all_trials(self):
  newer=copy.deepcopy(self.b)
  target=newer['results'][1]['scenario_id']
  newer['results'][1]['grade']['passed']=False
  newer['summary']=__import__('madset_eval.runs',fromlist=['summarize']).summarize(newer['results'])
  result=compare(self.b,newer)
  self.assertIn(target,result['regressions'])
  row=next(x for x in result['scenario_deltas'] if x['scenario_id']==target)
  self.assertLess(row['delta'],0)
 def test_human_review_template_is_blank(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.json';q=Path(d)/'reviews.csv';p.write_text(json.dumps(self.b),encoding='utf-8')
   export_template(p,q)
   data=q.read_text(encoding='utf-8-sig');self.assertIn('expert_1',data);self.assertIn('expert_2',data)
   self.assertIn('scenario_json',data);self.assertIn('recommendation',data)
   self.assertEqual(analyze_review(q)['status'],'NO_EXPERT_LABELS')
 def test_saved_transcript_can_be_regraded_without_rerun(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run.json';p.write_text(json.dumps(self.b),encoding='utf-8')
   rescored=regrade_run(p)
   self.assertEqual(len(rescored['results']),len(self.b['results']))
   self.assertEqual(rescored['metadata']['regraded_from_run_id'],self.b['metadata']['run_id'])
 def test_optional_judge_is_recorded(self):
  judged=exec_run('v3','dev',trials=1,save=False,judge_adapter='test_runs:fake_judge')
  self.assertEqual(judged['metadata']['judge_model_identifiers'],['mock/judge'])
  self.assertEqual(judged['metadata']['estimated_judge_cost_usd'],0.03)
  self.assertTrue(all('judge' in row['grade'] for row in judged['results']))
 def test_regrade_limit_and_unique_scenarios(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run.json';p.write_text(json.dumps(self.b),encoding='utf-8')
   judged=regrade_run(p,d,'test_runs:fake_judge',limit=2,unique_scenarios=True)
   self.assertEqual(len(judged['results']),2)
   self.assertEqual(len({x['scenario_id'] for x in judged['results']}),2)
   self.assertEqual(judged['metadata']['judge_input_tokens'],20)
   self.assertEqual(judged['metadata']['judge_output_tokens'],10)
   self.assertEqual(judged['metadata']['estimated_judge_cost_usd'],0.002)
   self.assertEqual(judged['results'][0]['judge_metadata']['model_identifier'],'mock/judge')
   self.assertTrue((Path(d)/'run_judging_partial.json').exists())
   resumed=regrade_run(p,d,'test_runs:fake_judge',limit=3,unique_scenarios=True,resume=True)
   self.assertEqual(len(resumed['results']),3)
   self.assertEqual(len({x['scenario_id'] for x in resumed['results']}),3)
 def test_saved_claude_run_can_be_repriced_without_api(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run.json'
   sample={'metadata':{},'results':[{'judge_metadata':{
    'model_version':'claude-sonnet-4-6','input_tokens':57952,'output_tokens':20395,'cost_usd':None}}]}
   p.write_text(json.dumps(sample),encoding='utf-8')
   result=reprice_claude_run(p)
   saved=json.loads(p.read_text(encoding='utf-8'))
   self.assertEqual(result['priced_judgments'],1)
   self.assertEqual(saved['metadata']['estimated_judge_cost_usd'],0.479781)
   self.assertEqual(saved['results'][0]['judge_metadata']['pricing_source'],'anthropic-list-price-2026-05-12')
 def test_repeated_judges_report_agreement_and_majority(self):
  with tempfile.TemporaryDirectory() as d:
   paths=[]
   decisions=((True,True),(True,False),(True,False))
   for index,values in enumerate(decisions):
    run={'metadata':{'judge_input_tokens':10,'judge_output_tokens':5,'estimated_judge_cost_usd':0.01},
         'summary':{'pass_rate':sum(values)/2,'avg_score':90},'results':[]}
    for scenario,passed in zip(('A','B'),values):
     run['results'].append({'scenario_id':scenario,'grade':{'passed':passed,'score':90 if passed else 70}})
    path=Path(d)/f'run{index}.json';path.write_text(json.dumps(run),encoding='utf-8');paths.append(path)
   result=analyze_judge_reliability(paths)
   self.assertEqual(result['summary']['unanimous_pass_decision_rate'],0.5)
   self.assertEqual(result['summary']['majority_pass_rate'],0.5)
   self.assertEqual(result['summary']['unstable_scenarios'],['B'])
   self.assertEqual(result['summary']['estimated_judge_cost_usd'],0.03)
