from madset_eval.runs import load_split
from madset_eval.contracts import generate_input
from examples.claude_adapter import advise
import json
scenario=load_split('dev')[0]
result=advise(generate_input(scenario))
print(json.dumps(result,ensure_ascii=False,indent=2))
