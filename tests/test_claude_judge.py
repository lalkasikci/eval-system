import unittest

from examples.claude_judge import JUDGE_TOOL, _extract_judgment


class ClaudeJudgeResponseTests(unittest.TestCase):
    def result(self):
        return {
            'decision_correct': True,
            'overall_pass': True,
            'dimension_scores': {
                'data_math': 4, 'diagnosis': 4, 'evidence_uncertainty': 4,
                'strategy': 4, 'economics_risk': 4, 'actionability': 4, 'clarity': 4,
            },
            'explanation': 'Uygun.',
            'violations': [],
        }

    def test_extracts_forced_tool_result(self):
        response = {'stop_reason': 'tool_use', 'content': [
            {'type': 'tool_use', 'name': JUDGE_TOOL['name'], 'input': self.result()}
        ]}
        self.assertEqual(_extract_judgment(response), self.result())
        structured = self.result()
        structured['violations'] = [{'code': 'missing_evidence', 'detail': 'Satış hunisi eksik'}]
        response['content'][0]['input'] = structured
        parsed = _extract_judgment(response)
        self.assertIsInstance(parsed['violations'][0], str)
        self.assertIn('missing_evidence', parsed['violations'][0])
        structured['explanation'] = ''
        parsed = _extract_judgment(response)
        self.assertIn('açıklama alanını boş bıraktı', parsed['explanation'])

    def test_empty_response_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, 'stop_reason'):
            _extract_judgment({'stop_reason': 'end_turn', 'content': []})
