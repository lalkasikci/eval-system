"""Versioned provider prices used only for transparent eval cost estimates."""
from __future__ import annotations

import os

ANTHROPIC_PRICES = {
    'claude-sonnet-4-6': {
        'input_usd_per_mtok': 3.0,
        'output_usd_per_mtok': 15.0,
        'effective_date': '2026-05-12',
        'source': 'anthropic-list-price-2026-05-12',
    },
}


def estimate_anthropic_cost(model, input_tokens, output_tokens):
    """Return an auditable estimate without requiring price env variables."""
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return {'cost_usd': None, 'pricing_source': 'usage-unavailable'}
    normalized=str(model or '').removeprefix('anthropic/')
    input_override=os.getenv('ANTHROPIC_INPUT_USD_PER_MTOK', '').strip()
    output_override=os.getenv('ANTHROPIC_OUTPUT_USD_PER_MTOK', '').strip()
    if bool(input_override) != bool(output_override):
        raise RuntimeError('ANTHROPIC_INPUT_USD_PER_MTOK ve ANTHROPIC_OUTPUT_USD_PER_MTOK birlikte verilmelidir')
    if input_override:
        input_rate=float(input_override);output_rate=float(output_override)
        effective=os.getenv('ANTHROPIC_PRICING_EFFECTIVE_DATE', '').strip() or 'user-supplied'
        source='environment-override'
    else:
        key=next((name for name in ANTHROPIC_PRICES if normalized==name or normalized.startswith(name+'-')),None)
        if not key:
            return {'cost_usd': None, 'pricing_source': 'unknown-model-price'}
        price=ANTHROPIC_PRICES[key]
        input_rate=price['input_usd_per_mtok'];output_rate=price['output_usd_per_mtok']
        effective=price['effective_date'];source=price['source']
    cost=(input_tokens*input_rate+output_tokens*output_rate)/1_000_000
    return {
        'cost_usd': round(cost,8),
        'input_usd_per_mtok': input_rate,
        'output_usd_per_mtok': output_rate,
        'pricing_effective_date': effective,
        'pricing_source': source,
    }
