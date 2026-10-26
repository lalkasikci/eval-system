"""Read-only HTTP adapter for the real Madset advice service.

The endpoint must accept synthetic scenario data and MUST NOT execute Meta writes.
"""
from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from madset_eval.contracts import validate_output

ADAPTER_VERSION='madset-http-adapter-v1'

def _normalize(body):
    # Supported real-service envelopes:
    # 1) the documented recommendation object directly
    # 2) {"recommendation": {...}, "usage": {...}, "model": "..."}
    result=body.get('recommendation') if isinstance(body,dict) and isinstance(body.get('recommendation'),dict) else body
    if not isinstance(result,dict):raise RuntimeError('Madset response does not contain a recommendation object')
    result=dict(result)
    usage=body.get('usage',{}) if isinstance(body,dict) else {}
    result['_eval_metadata']={
        'model_identifier':str(body.get('model') or body.get('engine') or 'madset/unknown') if isinstance(body,dict) else 'madset/unknown',
        'model_version':str(body.get('model_version') or body.get('version') or 'unknown') if isinstance(body,dict) else 'unknown',
        'prompt_version':str(body.get('prompt_version') or 'madset-owned') if isinstance(body,dict) else 'madset-owned',
        'input_tokens':usage.get('input_tokens') if isinstance(usage,dict) else None,
        'output_tokens':usage.get('output_tokens') if isinstance(usage,dict) else None,
        'cost_usd':usage.get('cost_usd') if isinstance(usage,dict) else None,
        'adapter_version':ADAPTER_VERSION,
    }
    validate_output({k:v for k,v in result.items() if k!='_eval_metadata'})
    return result

def advise(payload:dict)->dict:
    url=os.getenv('MADSET_ADVISE_URL','').strip()
    if not url:raise RuntimeError('MADSET_ADVISE_URL is required for the real Madset adapter')
    if not url.lower().startswith(('https://','http://localhost','http://127.0.0.1')):
        raise RuntimeError('MADSET_ADVISE_URL must use HTTPS or a localhost URL')
    token=os.getenv('MADSET_EVAL_TOKEN','').strip()
    request_body={
        'mode':'eval','dry_run':True,'synthetic':True,
        'scenario':payload,
        'constraints':{
            'advice_only':True,
            'forbid_platform_writes':True,
            'forbid_customer_data':True,
        },
    }
    headers={'content-type':'application/json','accept':'application/json',
             'x-madset-eval':'synthetic','x-madset-dry-run':'true'}
    if token:headers['authorization']='Bearer '+token
    data=json.dumps(request_body,ensure_ascii=False).encode('utf-8')
    for attempt in range(3):
        request=urllib.request.Request(url,data=data,headers=headers,method='POST')
        try:
            with urllib.request.urlopen(request,timeout=90) as response:
                body=json.load(response)
            if isinstance(body,dict) and body.get('write_performed') is True:
                raise RuntimeError('Madset eval endpoint reported a platform write; result rejected')
            return _normalize(body)
        except urllib.error.HTTPError as exc:
            detail=exc.read(500).decode('utf-8','replace')
            if exc.code in (429,500,502,503,504) and attempt<2:
                time.sleep(2**attempt);continue
            raise RuntimeError(f'Madset API HTTP {exc.code}: {detail}') from None
        except urllib.error.URLError as exc:
            if attempt<2:time.sleep(2**attempt);continue
            raise RuntimeError(f'Madset API connection failed: {exc.reason}') from None
    raise RuntimeError('Madset API did not return a response')
