"""Tool: llm_client

Thin wrapper around OpenRouter's OpenAI-compatible chat API. Reads the API
key and model from environment variables (loaded from .env by main.py).

Supports plain text-only requests and multimodal requests (text + screenshot
images), since screen requirements are often clearer as a picture than a
paragraph. Vision needs a vision-capable model — see OPENROUTER_VISION_MODEL
in .env.example.
"""
import base64
import json
import mimetypes
import os
from pathlib import Path

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
DEFAULT_VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct:free"


def _client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and paste your "
            "OpenRouter API key into it."
        )
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def _image_content_part(path: str) -> dict:
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    data = base64.b64encode(Path(path).read_bytes()).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def chat_json(instructions: str, task: str, image_paths: list[str] | None = None) -> dict:
    """Send a chat completion request and parse the reply as JSON.

    `instructions` is a skill's job description (what to do, what schema to
    return); this tool appends the "JSON only, no commentary" formatting
    constraint itself, since that's a mechanic of talking to any LLM, not
    something every skill should have to repeat.

    `image_paths`, if given, attaches screenshots to the user message and
    switches to OPENROUTER_VISION_MODEL — most free text models can't see
    images, so mixing the two silently would just get the images ignored.

    Raises ValueError if the model did not return valid JSON.
    """
    client = _client()

    if image_paths:
        model = os.environ.get("OPENROUTER_VISION_MODEL", DEFAULT_VISION_MODEL)
        user_content = [{"type": "text", "text": task}] + [_image_content_part(p) for p in image_paths]
    else:
        model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        user_content = task

    system_prompt = (
        f"{instructions}\n\n"
        "Respond with a single JSON object only — no markdown fences, no commentary "
        "before or after the JSON."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content or ""
    content = content.strip()

    # Free models sometimes wrap JSON in ```json fences despite instructions.
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model did not return valid JSON.\n---raw response---\n{content}"
        ) from exc
