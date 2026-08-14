#!/usr/bin/env python3
"""Small, token-light client for Poncho's programmable chat API.

The API key is read from ~/.hermes/.env and is never written to project files
or printed. Poncho's API is asynchronous: create a chat, then poll its result.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://tryponcho.com/api/v1"


def _load_key() -> str:
    key = os.environ.get("PONCHO_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    try:
        for line in env_path.read_text().splitlines():
            if line.startswith("PONCHO_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def _request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    key = _load_key()
    if not key:
        raise RuntimeError("PONCHO_API_KEY is not configured")
    body = None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Poncho API {exc.code}: {detail}") from exc


def create_chat(prompt: str) -> str:
    result = _request("/chats", "POST", {
        "text": prompt,
        "options": {"model": "claude-haiku-4-5", "thinking": "off"},
    })
    chat_id = result.get("chatId") or result.get("chat", {}).get("id")
    if not chat_id:
        raise RuntimeError(f"Poncho did not return chatId: {result}")
    return chat_id


def _parts_to_text(parts) -> str:
    out = []
    if isinstance(parts, str):
        return parts
    if isinstance(parts, list):
        for item in parts:
            out.append(_parts_to_text(item))
    elif isinstance(parts, dict):
        for key in ("text", "content", "value", "output"):
            if isinstance(parts.get(key), str):
                out.append(parts[key])
        for key in ("parts", "content", "messages"):
            if key in parts:
                out.append(_parts_to_text(parts[key]))
    return "\n".join(x for x in out if x)


def poll_chat(chat_id: str, timeout_s: int = 240) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        result = _request(f"/chats/{chat_id}/result")
        status = result.get("status")
        if status in ("finished", "idle"):
            texts = []
            snapshot = result.get("snapshot", {})
            for message in snapshot.get("messages", []):
                if message.get("role") == "assistant":
                    texts.append(_parts_to_text(message.get("parts", [])))
            text = "\n".join(x for x in texts if x).strip()
            if text:
                return text
            return json.dumps(result, ensure_ascii=False)
        if status in ("pending", "running"):
            time.sleep(3)
            continue
        raise RuntimeError(f"Unexpected Poncho status: {status}: {result}")
    raise TimeoutError(f"Poncho chat {chat_id} did not finish within {timeout_s}s")


def extract_json(text: str) -> dict:
    """Extract a JSON object from plain or fenced assistant output."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S | re.I)
    candidate = fenced.group(1) if fenced else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Poncho response contained no JSON object")
    return json.loads(candidate[start:end + 1])


def run_hot_lead_research(branch: str, region: str, max_results: int = 20, max_detail: int = 8) -> dict:
    prompt = f"""You are the research stage of Werkspree's lead pipeline. Do not send emails, do not create websites, and do not contact anyone.

Research at most {max_results} businesses for: {branch} in {region}, Germany. Use Google Maps or the StableEnrich Google Maps endpoint. Keep only businesses with Google Maps rating >= 4.4. Then deeply inspect at most {max_detail} highest-priority candidates.

For deep inspection, use StableEnrich/Exa for the official website and public Impressum/contact pages, and Hunter email verification only when a public business email was found. Treat OpenTable, Zenchef, Quandoo, Resmio, Tebi, Lieferando, Wolt, TripAdvisor, Yelp, Facebook and Instagram as third-party platforms, not official websites.

A hot lead requires ALL of: rating >= 4.4; clearly no official website or clearly outdated/dead website; publicly sourced business email; email_verified exactly yes; no guessed email. HTTP-only Maps URL without redirect, a free builder subdomain, or a very minimal/dead page may count as outdated only when supported by evidence. A current HTTPS site is not a hot lead. If status is unclear, reject it.

Return ONLY one JSON object (no markdown) with this exact shape:
{{"branch":"{branch}","region":"{region}","maps_results":0,"detail_pages_visited":0,"candidates":[],"hot_leads":[],"blocked_leads":[],"cost_usd":null}}

Each hot_leads item must include company_name, rating, review_count, price_level, full_business_address, official_company_website, website_status, business_email, email_source_url, email_verified, phone, evidence_notes, total_lead_cost_usd. Each blocked_leads item must include company_name and reason. Never invent values; use null or empty strings where unavailable. Include all relevant rejected candidates in blocked_leads. Do not use private/personal contact data."""
    chat_id = create_chat(prompt)
    text = poll_chat(chat_id)
    result = extract_json(text)
    result["poncho_chat_id"] = chat_id
    return result


if __name__ == "__main__":
    import sys
    branch = sys.argv[1] if len(sys.argv) > 1 else "restaurant"
    region = sys.argv[2] if len(sys.argv) > 2 else "Berlin"
    print(json.dumps(run_hot_lead_research(branch, region), ensure_ascii=False, indent=2))

