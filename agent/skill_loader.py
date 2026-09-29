"""Loads a SKILL.md file: YAML-style frontmatter (name, description) + a
markdown body. The body is the actual instructions handed to the LLM — a
skill here is plain instructions, not code.

Kept dependency-free with a small manual parser since our frontmatter is
just flat "key: value" pairs (no lists/nesting) — a full YAML parser would
be overkill for that.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    body: str


def load_skill(path: str) -> Skill:
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} has no frontmatter (expected to start with '---')")

    _, frontmatter, body = text.split("---", 2)
    meta = {}
    for line in frontmatter.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()

    return Skill(name=meta.get("name", ""), description=meta.get("description", ""), body=body.strip())
