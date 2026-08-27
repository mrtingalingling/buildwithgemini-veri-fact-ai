"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+),
with 15 queries/day rate limiting and Bring Your Own AI Model (BYOM - OpenAI, Claude, Gemini, Grok) remote auth support.
"""

import datetime
import os
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from google.protobuf.json_format import ParseDict
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    SendMessageRequest,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"
_A2UI_MIME = "application/json+a2ui"

_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }

app = FastAPI()

# --- Rate Limiter (15 queries per user per day) ---
_daily_usage: dict[str, dict] = {}
DAILY_LIMIT = 15

def _check_and_increment_rate_limit(user_id: str, has_byom_key: bool) -> tuple[bool, int]:
    """Returns (is_allowed, remaining_queries_count)"""
    if has_byom_key:
        return True, 999  # Uncapped access with own API key

    today_str = datetime.date.today().isoformat()
    user_entry = _daily_usage.get(user_id, {"date": today_str, "count": 0})

    if user_entry["date"] != today_str:
        user_entry = {"date": today_str, "count": 0}

    if user_entry["count"] >= DAILY_LIMIT:
        return False, 0

    user_entry["count"] += 1
    _daily_usage[user_id] = user_entry
    remaining = DAILY_LIMIT - user_entry["count"]
    return True, remaining

@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )

_contexts: dict[str, str] = {}
_card: AgentCard | None = None

async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        card = AgentCard()
        ParseDict(resp.json(), card, ignore_unknown_fields=True)
        for interface in card.supported_interfaces:
            interface.url = A2A_BASE
        _card = card
    return _card

def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        text = getattr(root, "text", None)
        if text:
            out.append({"kind": "text", "text": text})
            continue

        data = getattr(root, "data", None)
        print(f"DEBUG: data type: {type(data)}", flush=True)
        if data is not None:
            # When hitting the Agent Runtime via A2A, the entire types.Part dict
            # might get serialized into the 'data' Struct.
            metadata = getattr(root, "metadata", None)
            
            # If metadata isn't on the root part, check if it's nested inside the data struct
            data_struct = None
            if hasattr(data, "struct_value"):
                data_struct = data.struct_value
                print(f"DEBUG: got data.struct_value", flush=True)
            elif hasattr(data, "fields"):
                data_struct = data
                print(f"DEBUG: got data.fields", flush=True)
                
            if not metadata and data_struct is not None and "metadata" in getattr(data_struct, "fields", {}):
                print(f"DEBUG: Found metadata inside data_struct!", flush=True)
                metadata_val = data_struct.fields["metadata"]
                if hasattr(metadata_val, "struct_value"):
                    metadata = metadata_val.struct_value
                    print(f"DEBUG: got metadata.struct_value", flush=True)
                    
            mime = None
            if metadata:
                print(f"DEBUG: Checking metadata fields. type={type(metadata)}", flush=True)
                if hasattr(metadata, "get"):
                    mime = metadata.get("mimeType")
                elif hasattr(metadata, "fields"):
                    mime_field = getattr(metadata, "fields", {}).get("mimeType")
                    if mime_field:
                        mime = getattr(mime_field, "string_value", None)
            
            print(f"DEBUG: mime={mime}", flush=True)
            
            if mime == _A2UI_MIME:
                # Need to extract the actual 'data' payload from the parent data struct
                # If it's a struct, we need to convert it to a python dict/list
                data_val = data
                if data_struct is not None and "data" in data_struct.fields:
                    inner_data_val = data_struct.fields["data"]
                    if hasattr(inner_data_val, "struct_value"):
                        from google.protobuf.json_format import MessageToDict
                        # The inner 'data' contains the actual JSON payload
                        try:
                            # A2UI payloads are JSON strings, or list of dicts.
                            # We can just convert the struct to a dict.
                            data_val = MessageToDict(inner_data_val.struct_value)
                        except Exception as e:
                            print(f"DEBUG: MessageToDict failed: {e}", flush=True)
                    elif hasattr(inner_data_val, "string_value"):
                        data_val = inner_data_val.string_value
                        
                if hasattr(data_val, "decode"):
                    try:
                        data_val = data_val.decode("utf-8")
                    except Exception:
                        pass
                
                print(f"DEBUG: APPENDING A2UI PART", flush=True)
                out.append({"kind": "a2ui", "data": data_val})
                continue
                
        url = getattr(root, "url", None)
        if url:
            out.append({"kind": "text", "text": url})
            continue
            
        filename = getattr(root, "filename", None)
        if filename:
            out.append({"kind": "text", "text": filename})
            continue

        file_obj = getattr(root, "file", None)
        if file_obj:
            uri = getattr(file_obj, "uri", None)
            if uri:
                out.append({"kind": "text", "text": uri})
    return out

# --- External BYOM AI Provider Dispatcher ---
async def _query_byom_provider(provider: str, api_key: str, model: str, message: str) -> list[dict]:
    """Queries third-party AI models (OpenAI, Anthropic Claude, Gemini, Grok, Ollama/Custom)."""
    system_prompt = "You are VeriFact AI, a claim verification assistant. Fact-check claims accurately with sources, verdicts (True/False/Misleading), and confidence."
    
    async with httpx.AsyncClient(timeout=60) as client:
        if provider == "openai":
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model or "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ]
                }
            )
            res.raise_for_status()
            data = res.json()
            answer = data["choices"][0]["message"]["content"]
            return [{"kind": "text", "text": f"🤖 **[OpenAI {model or 'gpt-4o'}]**\n\n{answer}"}]

        elif provider == "anthropic":
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": message}]
                }
            )
            res.raise_for_status()
            data = res.json()
            answer = data["content"][0]["text"]
            return [{"kind": "text", "text": f"🧠 **[Anthropic Claude {model or '3.5-Sonnet'}]**\n\n{answer}"}]

        elif provider == "gemini":
            target_model = model or "gemini-2.5-flash"
            res = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Query: {message}"}]}]
                }
            )
            res.raise_for_status()
            data = res.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
            return [{"kind": "text", "text": f"✨ **[Google Gemini ({target_model})]**\n\n{answer}"}]

        elif provider in ["grok", "custom"]:
            endpoint = "https://api.x.ai/v1/chat/completions" if provider == "grok" else "https://openrouter.ai/api/v1/chat/completions"
            res = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model or ("grok-2-latest" if provider == "grok" else "auto"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ]
                }
            )
            res.raise_for_status()
            data = res.json()
            answer = data["choices"][0]["message"]["content"]
            return [{"kind": "text", "text": f"⚡ **[{provider.upper()} - {model or 'custom'}]**\n\n{answer}"}]

        else:
            raise ValueError(f"Unsupported provider: {provider}")

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    byom = body.get("byom") or {}

    provider = byom.get("provider", "").lower()
    api_key = byom.get("api_key", "").strip() if isinstance(byom.get("api_key"), str) else ""
    model_name = byom.get("model", "").strip() if isinstance(byom.get("model"), str) else ""

    has_byom_key = bool(api_key and provider and provider != "default")

    # Enforce 15 Queries/Day Rate Limit
    allowed, remaining = _check_and_increment_rate_limit(user_id, has_byom_key)
    if not allowed:
        return JSONResponse({
            "error": "DAILY_RATE_LIMIT_EXCEEDED",
            "remaining": 0,
            "parts": [{
                "kind": "text",
                "text": "⚠️ **Daily Free Query Limit Reached (15/15)**\n\n"
                        "You have used your 15 free daily fact-check queries.\n\n"
                        "🔑 **Bring Your Own AI Model (BYOM)**: Open **Remote AI Auth / BYOM Settings** (🔑) above to connect your own API Key (**OpenAI, Claude, Gemini, Grok, or OpenRouter**) for queries **WITHOUT CAP**!"
            }]
        })

    # Dispatch to custom provider if BYOM key is supplied
    if has_byom_key:
        try:
            parts = await _query_byom_provider(provider, api_key, model_name, message)
            return JSONResponse({"parts": parts, "remaining": 999, "provider": provider})
        except Exception as e:
            return JSONResponse({
                "parts": [{
                    "kind": "text",
                    "text": f"❌ **BYOM Provider Error ({provider.upper()})**: {e}\n\nFalling back to default Reasoning Engine..."
                }]
            })

    # Default: Route to Google Cloud Vertex AI Reasoning Engine over A2A
    parts: list[dict] = []
    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(ClientConfig(httpx_client=client))
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
            context_id=_contexts.get(user_id),
        )

        last_task = None
        got_artifact_update = False
        req_obj = SendMessageRequest(message=msg)
        async for event in a2a_client.send_message(req_obj):
            if event.HasField('task'):
                last_task = event.task
                if event.task.context_id:
                    _contexts[user_id] = event.task.context_id
            
            if event.HasField('artifact_update'):
                got_artifact_update = True
                if event.artifact_update.context_id:
                    _contexts[user_id] = event.artifact_update.context_id
                print("RAW ARTIFACT PARTS:", event.artifact_update.artifact.parts, flush=True)
                parts.extend(_extract_parts(event.artifact_update.artifact.parts))

        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(artifact.parts))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]

    return JSONResponse({"parts": parts, "remaining": remaining})

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
