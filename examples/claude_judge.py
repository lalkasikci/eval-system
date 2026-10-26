"""Claude semantic judge for Madset Eval Lab.

The API key is read only from ANTHROPIC_API_KEY and is never returned or logged.
Only synthetic scenario data, the candidate answer, and evaluator-side expectations
are sent. This module never calls an advertising platform.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

from madset_eval.contracts import WEIGHTS
from madset_eval.judging import validate_judge_output

MODEL = os.getenv('ANTHROPIC_JUDGE_MODEL', os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6'))
API_VERSION = os.getenv('ANTHROPIC_API_VERSION', '2023-06-01')
PROMPT_VERSION = 'madset-claude-judge-v1'

JUDGE_TOOL = {
    'name': 'submit_evaluation',
    'description': 'Submit the final rubric evaluation for the supplied synthetic advertising recommendation.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'decision_correct': {'type': 'boolean'},
            'overall_pass': {'type': 'boolean'},
            'dimension_scores': {
                'type': 'object',
                'properties': {key: {'type': 'integer', 'minimum': 0, 'maximum': 4} for key in WEIGHTS},
                'required': list(WEIGHTS),
                'additionalProperties': False,
            },
            'explanation': {'type': 'string', 'minLength': 1},
            'violations': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['decision_correct', 'overall_pass', 'dimension_scores', 'explanation', 'violations'],
        'additionalProperties': False,
    },
}

SYSTEM = """Sen Madset Advise Lab için tarafsız bir değerlendirme yargıcısın.
Yalnız verilen sentetik senaryoyu, aday öneriyi, beklentiyi ve rubric'i kullan.
Reklam platformunda işlem yapma veya dış veri kullanma. Referans metne kelime kelime
benzerlik arama; anlamı değerlendir. Matematik ve kritik güvenlik hataları ayrıca kodla
denetlenir, fakat gördüğün anlamsal sorunları violations alanında belirt.

Tam olarak şu JSON biçimini döndür, markdown kullanma:
{"decision_correct":true,"overall_pass":true,"dimension_scores":{"data_math":4,"diagnosis":4,"evidence_uncertainty":4,"strategy":4,"economics_risk":4,"actionability":4,"clarity":4},"explanation":"kısa gerekçe","violations":[]}

Her boyut 0-4 tam sayı olmalı. overall_pass yalnız öneri güvenli, doğru, senaryoya özgü,
uygulanabilir ve beklentideki must_include/must_not_include koşullarıyla uyumluysa true olsun.
Kararsızsan daha düşük puan ver ve gerekçeyi açıkla."""


def _json_object(text):
    value = text.strip()
    if not value:
        raise ValueError('Claude yanıtında metin veya değerlendirme aracı bulunamadı')
    if value.startswith('```'):
        value = re.sub(r'^```(?:json)?\s*', '', value)
        value = re.sub(r'\s*```$', '', value)
    return json.loads(value)


def _extract_judgment(response_data):
    content = response_data.get('content') or []
    for block in content:
        if block.get('type') == 'tool_use' and block.get('name') == JUDGE_TOOL['name']:
            result = block.get('input')
            if not isinstance(result, dict):
                raise ValueError('Claude değerlendirme aracı nesne döndürmedi')
            violations = result.get('violations')
            if violations is None:
                result['violations'] = []
            elif not isinstance(violations, list):
                result['violations'] = [str(violations)]
            else:
                result['violations'] = [
                    item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, sort_keys=True)
                    for item in violations
                ]
            if not isinstance(result.get('explanation'), str) or not result['explanation'].strip():
                if result['violations']:
                    result['explanation'] = 'Claude açıklama alanını boş bıraktı; bildirilen ihlaller: ' + '; '.join(result['violations'])
                else:
                    result['explanation'] = 'Claude yapılandırılmış puanları döndürdü ancak açıklama alanını boş bıraktı.'
            return result
    text = '\n'.join(block.get('text', '') for block in content if block.get('type') == 'text').strip()
    if text:
        return _json_object(text)
    types = sorted({str(block.get('type', 'unknown')) for block in content})
    raise ValueError(
        'Claude yapılandırılmış değerlendirme döndürmedi; '
        f'stop_reason={response_data.get("stop_reason")!r}, content_types={types}'
    )


def judge(payload):
    key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not key:
        raise RuntimeError('ANTHROPIC_API_KEY bulunamadı; anahtarı sohbet veya kaynak dosyasına yazmayın')
    request_payload = {
        'scenario': payload['input'],
        'candidate': payload['output'],
        'expectation': payload['expectation'],
        'rubric': {'dimensions': list(WEIGHTS), 'weights': WEIGHTS, 'pass_threshold': 80},
    }
    body = {
        'model': MODEL,
        'max_tokens': 1200,
        'temperature': 0,
        'system': SYSTEM,
        'messages': [{'role': 'user', 'content': json.dumps(request_payload, ensure_ascii=False, sort_keys=True)}],
        'tools': [JUDGE_TOOL],
        'tool_choice': {'type': 'tool', 'name': JUDGE_TOOL['name']},
    }
    headers = {'content-type': 'application/json', 'anthropic-version': API_VERSION, 'x-api-key': key}
    workspace = os.getenv('ANTHROPIC_WORKSPACE_ID', '').strip()
    if workspace:
        headers['anthropic-workspace-id'] = workspace
    try:
        timeout_seconds = float(os.getenv('ANTHROPIC_TIMEOUT_SECONDS', '30'))
    except ValueError:
        raise RuntimeError('ANTHROPIC_TIMEOUT_SECONDS sayısal olmalıdır') from None
    if not 5 <= timeout_seconds <= 120:
        raise RuntimeError('ANTHROPIC_TIMEOUT_SECONDS 5 ile 120 arasında olmalıdır')
    request = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response_data = json.load(response)
            result = _extract_judgment(response_data)
            result['provider'] = 'anthropic'
            result['model'] = str(response_data.get('model') or MODEL)
            validate_judge_output(result)
            usage = response_data.get('usage') or {}
            input_tokens = usage.get('input_tokens')
            output_tokens = usage.get('output_tokens')
            input_rate = os.getenv('ANTHROPIC_INPUT_USD_PER_MTOK', '').strip()
            output_rate = os.getenv('ANTHROPIC_OUTPUT_USD_PER_MTOK', '').strip()
            cost = None
            if input_rate and output_rate and isinstance(input_tokens, int) and isinstance(output_tokens, int):
                cost = (input_tokens * float(input_rate) + output_tokens * float(output_rate)) / 1_000_000
            result['_eval_metadata'] = {
                'model_identifier': 'anthropic/' + result['model'],
                'model_version': result['model'],
                'prompt_version': PROMPT_VERSION,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost,
            }
            return result
        except urllib.error.HTTPError as exc:
            safe_message = exc.read(400).decode('utf-8', 'replace')
            if exc.code in (429, 500, 502, 503, 529) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f'Claude judge HTTP {exc.code}: {safe_message}') from None
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError(f'Claude judge bağlantı/zaman aşımı hatası: {type(exc).__name__}') from None
    raise RuntimeError('Claude judge yanıt veremedi')
