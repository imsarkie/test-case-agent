"""Tool: normalize_test_cases

Turns the raw JSON returned by the LLM (per skills/generate-test-cases/SKILL.md's
schema) into row dicts matching the xlsx column layout in tools/write_excel.py.
Purely mechanical — no LLM calls here.
"""


def normalize_test_cases(raw: dict, req_id: str, module: str) -> list[dict]:
    raw_cases = raw.get("test_cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("Model response did not contain a 'test_cases' list.")

    cases = []
    for i, c in enumerate(raw_cases, start=1):
        cases.append({
            "req_id": req_id,
            "req_description": None,
            "test_case_id": f"TC_{req_id}_{i:03d}",
            "module": module,
            "title": c.get("title", ""),
            "precondition": c.get("precondition", ""),
            "steps": c.get("steps", []),
            "test_data": c.get("test_data", []),
            "expected_result": c.get("expected_result", ""),
            "priority": c.get("priority", ""),
            "type": c.get("type", ""),
            "execution": "Manual",
        })
    return cases
