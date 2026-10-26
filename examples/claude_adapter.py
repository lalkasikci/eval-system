"""Claude API integration for Madset Eval Lab. Uses standard library only.
Only synthetic input is sent. Gold expectations and IDs are never included.
"""
import os, json, urllib.request, urllib.error, time, re
from madset_eval.contracts import validate_output, derived_metrics

MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6')
API_VERSION = os.getenv('ANTHROPIC_API_VERSION', '2023-06-01')
PROMPT_VERSION = 'madset-claude-eval-v1'
SYSTEM = """Sen Madset'in reklam tavsiye asistanısın. Senaryolar sentetiktir. Reklam verisini iş sahibi için doğru, ihtiyatlı ve uygulanabilir şekilde yorumla. Yalnızca JSON nesnesi döndür, markdown kullanma.
Karar sınıfları: ACT, WAIT, DIAGNOSE, MEASURE, MAINTAIN.
Yalnızca eldeki sayılara dayan; veri eksikliğini sıfır sonuç sayma, nedensellik uydurma, kesin satış vaat etme, izinsiz işlem yapma. Platforma özel aksiyonu başka platforma önerme. Dış API'leri çağırma.
Çıktı şeması:
{"decision":"WAIT","recommendation":"kısa düz Türkçe öneri","rationale":"somut dayanak","next_step":"tek sonraki adım","uncertainty":"bilinmeyenleri belirt","risk":"ticari riskleri belirt","evidence":[{"key":"spend","value":600}],"claims":{"spend":600},"action":{"type":"observe"}}
Evidence ve claims yalnızca girdi metriklerinden veya matematiksel türetilebilir alanlardan seçilmeli. Diğer sayı ve iddiaları sayısal claim olarak ekleme. Action type için observe, audit_tracking, audit_funnel, test_offer, increase_budget, pause_campaign, diagnose veya maintain kullan. Değişiklik yapıldığı iddiası kurma."""

def _json_object(text):
    t=text.strip()
    if t.startswith('```'):
        t=re.sub(r'^```(?:json)?\s*','',t)
        t=re.sub(r'\s*```$','',t)
    return json.loads(t)

def advise(payload: dict)->dict:
    key=os.getenv('ANTHROPIC_API_KEY','').strip()
    if not key: raise RuntimeError('ANTHROPIC_API_KEY bulunamadı. Anahtarı yalnızca kendi terminalinizde ortam değişkeni olarak ayarlayın.')
    # Avoid sending scenario labels or expected answers. Runner already strips these.
    data={k:v for k,v in payload.items() if k not in ('scenario_id','id','expectation','allowed_decisions','gold')}
    request_body={'model':MODEL,'max_tokens':1200,'temperature':0,
        'system':SYSTEM,
        'messages':[{'role':'user','content':'Sentetik reklam senaryosu:\n'+json.dumps(data,ensure_ascii=False,sort_keys=True)+'\nTüretilmiş metrikler (null=ölçülemiyor):\n'+json.dumps(derived_metrics(data),ensure_ascii=False,sort_keys=True)}]}
    headers={'content-type':'application/json','anthropic-version':API_VERSION,'x-api-key':key}
    workspace=os.getenv('ANTHROPIC_WORKSPACE_ID','').strip()
    if workspace:headers['anthropic-workspace-id']=workspace
    req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=json.dumps(request_body,ensure_ascii=False).encode(),headers=headers,method='POST')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=75) as response:
                response_data=json.load(response)
            text='\n'.join(c['text'] for c in response_data.get('content',[]) if c.get('type')=='text')
            result=_json_object(text)
            validate_output(result)
            usage=response_data.get('usage') or {}
            input_tokens=usage.get('input_tokens');output_tokens=usage.get('output_tokens')
            input_rate=os.getenv('ANTHROPIC_INPUT_USD_PER_MTOK','').strip()
            output_rate=os.getenv('ANTHROPIC_OUTPUT_USD_PER_MTOK','').strip()
            cost=None
            if input_rate and output_rate and isinstance(input_tokens,int) and isinstance(output_tokens,int):
                cost=(input_tokens*float(input_rate)+output_tokens*float(output_rate))/1_000_000
            result['_eval_metadata']={
                'model_identifier':'anthropic/'+str(response_data.get('model') or MODEL),
                'model_version':str(response_data.get('model') or MODEL),
                'prompt_version':PROMPT_VERSION,
                'input_tokens':input_tokens,'output_tokens':output_tokens,'cost_usd':cost,
            }
            return result
        except urllib.error.HTTPError as exc:
            message=exc.read(400).decode('utf-8','replace')
            # Never reveal API key, or include authentication header.
            if exc.code in (429,500,502,503,529) and attempt<2:
                time.sleep(2**attempt);continue
            raise RuntimeError(f'Claude API HTTP {exc.code}: {message}') from None
    raise RuntimeError('Claude API yanıt veremedi')
