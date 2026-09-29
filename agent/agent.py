"""Agent: TestCaseAgent

The orchestrator. It doesn't know how to read documents, call the LLM, or
write Excel files itself — it delegates each of those to a tool. It doesn't
know how to write good test cases either — that instruction set lives in
skills/generate-test-cases/SKILL.md, a plain markdown file the agent loads
and hands to the LLM. This separation (agent = orchestration, skills =
instructions, tools = concrete actions) is the same pattern Claude Code
itself uses, kept intentionally small here for learning purposes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.skill_loader import load_skill
from tools.llm_client import chat_json
from tools.normalize_test_cases import normalize_test_cases
from tools.read_document import read_document
from tools.write_excel import write_test_cases_to_excel

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "generate-test-cases" / "SKILL.md"


class TestCaseAgent:
    def run(
        self,
        input_path: str,
        req_id: str,
        module: str,
        output_path: str,
        count_hint: int | None = None,
        screenshots: list[str] | None = None,
    ) -> list[dict]:
        print(f"[agent] reading document: {input_path}")
        document_text = read_document(input_path)

        print(f"[agent] loading skill: {SKILL_PATH.parent.name}")
        skill = load_skill(str(SKILL_PATH))

        count_line = f"Generate approximately {count_hint} test cases.\n" if count_hint else ""
        task = (
            f"Module / screen: {module}\n"
            f"{count_line}"
            f"\n--- SOURCE DOCUMENT ---\n{document_text}\n--- END DOCUMENT ---"
        )

        if screenshots:
            print(f"[agent] attaching {len(screenshots)} screenshot(s): {', '.join(screenshots)}")

        print(f"[agent] calling LLM per skill '{skill.name}'")
        raw = chat_json(skill.body, task, image_paths=screenshots)

        cases = normalize_test_cases(raw, req_id=req_id, module=module)

        print(f"[agent] writing {len(cases)} test cases to: {output_path}")
        write_test_cases_to_excel(cases, output_path)

        return cases
