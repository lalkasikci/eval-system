import unittest

from madset_eval.contracts import WEIGHTS
from madset_eval.judging import merge_judgment,validate_judge_output


class JudgeContractTests(unittest.TestCase):
    def judgment(self):
        return {'decision_correct':True,'overall_pass':True,
                'dimension_scores':{key:4 for key in WEIGHTS},
                'explanation':'Senaryoya uygun ve güvenli.','violations':[]}

    def base(self,codes=None):
        return {'decision_correct':True,'expected_decisions':['WAIT'],'score':80,
                'dimension_scores':{key:3 for key in WEIGHTS},'semantic':{},
                'critical_codes':codes or [],'critical_details':[],'passed':True,'limitations':[]}

    def test_valid_judgment_merges(self):
        result=merge_judgment(self.base(),self.judgment())
        self.assertTrue(result['passed']);self.assertEqual(result['score'],100)

    def test_code_hard_fail_overrides_llm(self):
        result=merge_judgment(self.base(['F05']),self.judgment())
        self.assertFalse(result['passed'])

    def test_rejects_incomplete_dimensions(self):
        value=self.judgment();value['dimension_scores'].pop('clarity')
        with self.assertRaises(ValueError):validate_judge_output(value)
