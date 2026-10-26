import os,unittest
from unittest.mock import patch
from examples.madset_adapter import _normalize,advise

GOOD={'decision':'WAIT','recommendation':'Biraz daha veri bekleyin.',
      'rationale':'Kampanya yeni.','next_step':'Üç gün sonra kontrol edin.',
      'uncertainty':'Örneklem sınırlı.','risk':'Erken değişiklik yapmayın.',
      'evidence':[{'key':'spend','value':100}], 'claims':{'spend':100},
      'action':{'type':'observe'}}

class MadsetAdapterTests(unittest.TestCase):
 def test_normalizes_service_envelope_and_usage(self):
  out=_normalize({'recommendation':GOOD,'model':'madset-advisor','model_version':'7',
                  'prompt_version':'p3','usage':{'input_tokens':10,'output_tokens':20,'cost_usd':.01}})
  self.assertEqual(out['decision'],'WAIT')
  self.assertEqual(out['_eval_metadata']['model_identifier'],'madset-advisor')
  self.assertEqual(out['_eval_metadata']['input_tokens'],10)
 def test_real_adapter_requires_endpoint(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(RuntimeError,'MADSET_ADVISE_URL'):
    advise({'synthetic':True})

if __name__=='__main__':unittest.main()
