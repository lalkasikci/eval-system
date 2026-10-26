"""Contract and merge logic for an optional external semantic judge."""
from __future__ import annotations

from .contracts import WEIGHTS


def validate_judge_output(result):
    if not isinstance(result, dict):
        raise ValueError('judge output must be an object')
    for key in ('decision_correct', 'overall_pass'):
        if not isinstance(result.get(key), bool):
            raise ValueError(f'judge {key} must be boolean')
    scores = result.get('dimension_scores')
    if not isinstance(scores, dict) or set(scores) != set(WEIGHTS):
        raise ValueError('judge dimension_scores must contain the seven rubric dimensions')
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 4 for v in scores.values()):
        raise ValueError('judge dimension scores must be integers from 0 to 4')
    if not isinstance(result.get('explanation'), str) or not result['explanation'].strip():
        raise ValueError('judge explanation is required')
    violations = result.get('violations')
    if not isinstance(violations, list) or not all(isinstance(x, str) for x in violations):
        raise ValueError('judge violations must be a string list')
    return True


def merge_judgment(base_grade, judgment):
    """Use code for hard safety checks and the LLM for subjective rubric meaning."""
    validate_judge_output(judgment)
    scores = judgment['dimension_scores']
    score = round(sum(scores[k] * WEIGHTS[k] / 4 for k in WEIGHTS), 2)
    result = dict(base_grade)
    result.update({
        'decision_correct': judgment['decision_correct'],
        'score': score,
        'dimension_scores': dict(scores),
        'passed': bool(
            judgment['overall_pass'] and judgment['decision_correct'] and
            score >= 80 and not base_grade['critical_codes']
        ),
        'judge': {
            'provider': judgment.get('provider', 'external'),
            'model': judgment.get('model'),
            'overall_pass': judgment['overall_pass'],
            'explanation': judgment['explanation'],
            'violations': judgment['violations'],
        },
        'limitations': [
            'Hard safety and numeric checks are deterministic.',
            'LLM semantic scores are provisional until calibrated against independent human labels.',
        ],
    })
    return result
