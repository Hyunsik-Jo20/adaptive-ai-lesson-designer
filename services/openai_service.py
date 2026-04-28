from __future__ import annotations
import base64, json, re
from pathlib import Path
from openai import OpenAI

def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text

def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

def image_to_data_url(path: str | Path) -> str:
    path = Path(path)
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    raw = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{raw}"

def call_json(client: OpenAI, model: str, prompt: str) -> dict:
    resp = client.responses.create(model=model, input=prompt, temperature=0.2)
    text = getattr(resp, "output_text", "") or str(resp)
    return json.loads(_strip_json(text))

def call_vision_json(client: OpenAI, model: str, prompt: str, image_paths: list[str]) -> dict:
    content = [{"type": "input_text", "text": prompt}]
    for p in image_paths:
        content.append({"type": "input_image", "image_url": image_to_data_url(p)})
    resp = client.responses.create(
        model=model,
        input=[{"role": "user", "content": content}],
        temperature=0.1,
    )
    text = getattr(resp, "output_text", "") or str(resp)
    return json.loads(_strip_json(text))
