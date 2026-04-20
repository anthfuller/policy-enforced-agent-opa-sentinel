from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

def get_azure_openai_client() -> AzureOpenAI:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    if not endpoint or not api_key:
        raise RuntimeError(
            "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY. "
            "Set these env vars to enable agent autonomy."
        )
    return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)

def chat_json(
    *,
    client: AzureOpenAI,
    deployment: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 900,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """Return a parsed JSON object from the model.

    We enforce JSON-only by requesting `response_format={"type":"json_object"}`.
    """
    resp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    # The SDK returns a string JSON payload when response_format is json_object.
    import json as _json
    return _json.loads(content)
