"""Example connector for your REAL Advise logic. Receives INPUT-ONLY synthetic payload.

Replace this toy producer with your local, version-pinned Madset interface.
No scenario ID, expected decision, test split or private answer is provided.
"""
from madset_eval.baselines import v3

def advise(payload: dict) -> dict:
    # Import Madset implementation and map its fields into documented output schema.
    # For illustration use the included offline rule baseline.
    return v3(payload)
