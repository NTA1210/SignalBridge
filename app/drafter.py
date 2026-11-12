"""Optional LLM drafting. Default to an auditable evidence-only template.

An explicit OPENAI_API_KEY and AI_PROVIDER=openai opt in to sending the
prospect evidence to OpenAI. Never call an LLM from the default demo.
"""
from __future__ import annotations
import os
import httpx
from .core import draft_from_evidence


def make_draft(person) -> tuple[str, str]:
    if os.getenv("AI_PROVIDER", "template").strip().lower() != "openai":
        return draft_from_evidence(person), "template"
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("AI_PROVIDER=openai needs OPENAI_API_KEY")
    system = (
        "Write ONE short, warm, professional outreach DM of at most 65 words. "
        "Use ONLY supplied evidence; no invented achievements, familiarity or prior relationship. "
        "Ask for a short, optional conversation; do not pressure. "
        "Do not include hashtags or promises. Return message only."
    )
    content = (f"Name: {person['display_name']}\nRole: {person['role']}\n"
               f"Bio: {person['bio']}\nVerified only as source-provided evidence, not independently validated:\n"
               f"{person['evidence_text']}\nSource: {person['evidence_url']}")
    with httpx.Client(timeout=20.0) as client:
        r = client.post("https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": "Bearer " + key},
                        json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                              "temperature": 0.4,
                              "max_tokens": 160,
                              "messages": [{"role": "system", "content": system},
                                           {"role": "user", "content": content}]})
        r.raise_for_status()
        body = (r.json()["choices"][0]["message"]["content"] or "").strip()
    if not body or len(body) > 1200:
        raise RuntimeError("LLM draft missing or longer than allowed")
    return body, "openai"
