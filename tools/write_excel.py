"""Tool: write_excel

Writes a list of test case dicts to an .xlsx file, using the same column
layout as the manual test-case workbooks in ../demo-project, so the output
stays compatible with that project's ingestion script if needed later.
"""
from pathlib import Path

import openpyxl

COLUMNS = [
    "Req ID",
    "Req Description",
    "Test Case ID",
    "Module",
    "Title",
    "Precondition",
    "Test Steps",
    "Test Data",
    "Expected Result",
    "Priority",
    "Type",
    "Execution",
]


def _join_lines(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def write_test_cases_to_excel(cases: list[dict], output_path: str, sheet_name: str = "Test Cases") -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(COLUMNS)

    for case in cases:
        row = [
            case.get("req_id", ""),
            case.get("req_description", ""),
            case.get("test_case_id", ""),
            case.get("module", ""),
            case.get("title", ""),
            case.get("precondition", ""),
            _join_lines(case.get("steps")),
            _join_lines(case.get("test_data")),
            case.get("expected_result", ""),
            case.get("priority", ""),
            case.get("type", ""),
            case.get("execution", ""),
        ]
        ws.append(row)

    for col_idx, header in enumerate(COLUMNS, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(15, len(header) + 2)

    wb.save(str(out))
