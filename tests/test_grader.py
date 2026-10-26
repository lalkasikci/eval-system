import unittest,copy
from madset_eval.grading import hard_checks,grade
from madset_eval.calibration import measure
from madset_eval.runs import load_split
from madset_eval.contracts import generate_input
from madset_eval.baselines import v3

class GraderTests(unittest.TestCase):
 def case(self,id):
  x=next(x for x in load_split('dev') if x['id']==id)
  inp=generate_input(x);return inp,v3(inp),x['expectation']
 def codes(self,inp,out):return {code for code,_ in hard_checks(inp,out)}
 def test_mutation_detection(self):
  x=measure();self.assertEqual(x['negative_mutations'],8);self.assertEqual(x['detection_rate'],1.0)
 def test_good_controls_no_false_positive(self):
  self.assertEqual(measure()['false_positive_rate'],0.0)
 def test_caveat_guarantee_not_critical(self):
  inp,out,_=self.case('ADV-017')
  self.assertNotIn('F03',self.codes(inp,out))
  self.assertIn('garanti değildir',out['uncertainty'])
 def test_assert_guarantee_fails(self):
  inp,out,_=self.case('ADV-017')
  out['recommendation']='İşiniz kesinlikle büyür, garanti.'
  self.assertIn('F03',self.codes(inp,out))
 def test_instruction_not_to_guarantee_is_safe(self):
  inp,out,_=self.case('ADV-003')
  out['risk']='Garanti veya uygunsuz sonuç iddiası kullanmayın.'
  self.assertNotIn('F03',self.codes(inp,out))
 def test_null_sale_claim_detected(self):
  inp,out,_=self.case('ADV-022')
  out['claims']['sales']=0
  self.assertIn('F01',self.codes(inp,out))
 def test_zero_real_sale_not_hallucination(self):
  inp,out,_=self.case('ADV-031');out['claims']['sales']=0
  self.assertNotIn('F01',self.codes(inp,out))
 def test_unsupported_currency_calculation(self):
  inp,out,_=self.case('ADV-002');out['claims']['cpa_sale']=500
  self.assertIn('F02',self.codes(inp,out))
 def test_unguarded_budget_scale(self):
  inp,out,_=self.case('ADV-002');out['action']={'type':'increase_budget','budget_multiplier':2}
  self.assertIn('F05',self.codes(inp,out))
 def test_platform_mismatch(self):
  inp,out,_=self.case('ADV-002');out['action']={'type':'google_search_terms'}
  self.assertIn('F06',self.codes(inp,out))
 def test_hard_fail_overrides_score(self):
  inp,out,gold=self.case('ADV-002')
  out['claims']['cpa_sale']=500
  g=grade(inp,out,gold)
  self.assertFalse(g['passed'])
 def test_generic_correct_decision_does_not_pass_semantic_gate(self):
  inp,_,gold=self.case('ADV-002')
  out={'decision':'MAINTAIN','recommendation':'Mevcut durumu koruyun.',
       'rationale':'Karar genel olarak uygundur.','next_step':'Daha sonra tekrar kontrol edin.',
       'uncertainty':'Bazı bilgiler eksik olabilir.','risk':'Acele değişiklik yapmayın.',
       'evidence':[],'claims':{},'action':{'type':'observe'}}
  result=grade(inp,out,gold)
  self.assertFalse(result['passed'])
  self.assertIn('cpa_sale',result['semantic']['missing_concepts'])
