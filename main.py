#!/usr/bin/env python3
"""Entry point for the test-case-generation agent.

Usage:
    python3 main.py --input input/sample_frd.md --req FR-USR-01 --module "User Directory" --out output/fr-usr-01.xlsx
    python3 main.py --input input/sample_frd.md --req FR-USR-01 --module "User Directory" --out output/fr-usr-01.xlsx --screenshots input/screenshots/directory.png
"""
import argparse

from dotenv import load_dotenv

from agent.agent import TestCaseAgent


def main():
    load_dotenv()

    ap = argparse.ArgumentParser(description="Generate manual test cases from a requirement document.")
    ap.add_argument("--input", required=True, help="Path to the source document (.txt, .md, .docx, .pdf)")
    ap.add_argument("--req", required=True, help="Requirement ID, e.g. FR-USR-01")
    ap.add_argument("--module", required=True, help="Module / screen name, e.g. 'User Directory'")
    ap.add_argument("--out", required=True, help="Output .xlsx path, e.g. output/fr-usr-01.xlsx")
    ap.add_argument("--count", type=int, default=None, help="Approximate number of test cases to generate")
    ap.add_argument(
        "--screenshots",
        nargs="*",
        default=None,
        help="Paths to screenshot images of the screen (.png/.jpg). Requires a vision-capable model — see OPENROUTER_VISION_MODEL in .env.example.",
    )
    args = ap.parse_args()

    agent = TestCaseAgent()
    cases = agent.run(
        input_path=args.input,
        req_id=args.req,
        module=args.module,
        output_path=args.out,
        count_hint=args.count,
        screenshots=args.screenshots,
    )
    print(f"Done. {len(cases)} test cases written to {args.out}")


if __name__ == "__main__":
    main()
