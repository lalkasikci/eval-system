import unittest,copy
from madset_eval.contracts import validate_input,derived_metrics,generate_input,ContractError,validate_output
from madset_eval.runs import load_split,validate_suite
from madset_eval.baselines import v3

class ContractTests(unittest.TestCase):
 def setUp(self):self.dev=load_split('dev');self.hold=load_split('holdout')
 def test_dataset_partition(self):
  val=validate_suite();self.assertTrue(val['valid'],val['errors']);self.assertEqual(val['total'],40);self.assertEqual(val['holdout_v2'],12);self.assertEqual(val['total_with_new_holdout'],52);self.assertEqual(val['holdout_rate'],.25)
  self.assertFalse({x['id'] for x in self.dev}&{x['id'] for x in self.hold})
 def test_all_valid(self):
  for x in self.dev+self.hold:self.assertTrue(validate_input(x['input']))
 def test_gold_not_in_holdout_input(self):
  for item in self.hold:self.assertNotIn('expectation',item)
 def test_producer_input_has_no_gold_or_id(self):
  for item in self.dev+self.hold:
   inp=generate_input(item)
   for key in ('expectation','allowed_decisions','id','group','scenario_id'):
    self.assertNotIn(key,inp)
 def test_derived_math(self):
  case=next(x for x in self.dev if x['id']=='ADV-002')
  d=derived_metrics(case['input'])
  self.assertAlmostEqual(d['cpa_sale'],250)
  self.assertAlmostEqual(d['roas'],3.2)
 def test_unknown_sales_not_zero(self):
  case=next(x for x in self.dev if x['id']=='ADV-022');d=derived_metrics(case['input'])
  self.assertIsNone(d['roas']);self.assertIsNone(d['cpa_sale'])
 def test_divide_by_zero_is_null(self):
  case=next(x for x in self.hold if x['id']=='ADV-037')
  d=derived_metrics(case['input']);self.assertIsNone(d['cpc']);self.assertIsNone(d['cpl'])
 def test_invalid_metrics_rejected(self):
  case=copy.deepcopy(self.dev[0]['input']);case['metrics']['clicks']=999999
  with self.assertRaises(ContractError):validate_input(case)
 def test_invalid_sales_measurement_rejected(self):
  case=copy.deepcopy(self.dev[0]['input']);case['availability']['sales_measured']=False
  with self.assertRaises(ContractError):validate_input(case)
 def test_output_schema(self):
  for case in self.dev:
   self.assertTrue(validate_output(v3(generate_input(case))))
