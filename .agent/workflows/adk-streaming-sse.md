---
description: Enable SSE (Server-Sent Events) streaming for text-based ADK agents with HTTP streaming responses
---

# ADK Workflow: SSE Streaming

Configure ADK agents to use Server-Sent Events (SSE) streaming mode for text-based interactions with HTTP streaming responses.

---

## When to Use SSE Mode

Use `StreamingMode.SSE` when:

- Building text-based chat applications
- Standard request/response interaction pattern
- Using models without Live API support (e.g., Gemini 1.5 Pro, Gemini 1.5 Flash)
- Simpler deployment without WebSocket requirements
- Need larger context windows (Gemini 1.5 supports up to 2M tokens)
- Prefer standard API rate limits (RPM/TPM) over concurrent session quotas

**Do NOT use SSE when:**

- Building voice/video applications with real-time interaction
- Need bidirectional communication (send while receiving)
- Require Live API features (audio transcription, VAD, proactivity)
- Supporting interruptions and natural turn-taking

---

## Prerequisites

- [ ] ADK agent configured with appropriate model
- [ ] For Gemini 1.5 models: SSE is the only supported streaming mode

```python
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
```

---

## Step 1: Configure StreamingMode.SSE

SSE mode uses HTTP streaming to connect to the standard Gemini API via `generate_content_async()`.

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

# SSE streaming for text-based interactions
run_config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    response_modalities=["TEXT"]  # Text-only modality
)
```

SSE mode uses the **unidirectional HTTP streaming** protocol:

1. You send a complete request upfront
2. Receive the response as a stream of chunks
3. Each chunk has `partial=True` until the final chunk with `finish_reason=STOP`

---

## Step 2: Use Runner.run() or run_async()

For SSE streaming, use the synchronous `run()` generator or async `run_async()` generator.

### Synchronous Pattern

```python
from google.adk.runners import Runner
from google.genai import types

runner = Runner(app_name="my-app", agent=agent, session_service=session_service)

# Create user message
new_message = types.Content(parts=[types.Part(text="Hello, how are you?")])

# Iterate over streaming events
for event in runner.run(
    user_id="user-123",
    session_id="session-456",
    new_message=new_message,
    run_config=run_config
):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                print(part.text, end="", flush=True)
```

### Async Pattern

```python
async for event in runner.run_async(
    user_id="user-123",
    session_id="session-456",
    new_message=new_message,
    run_config=run_config
):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                await websocket.send_text(part.text)
```

---

## Step 3: Serialize Events for SSE Transport

ADK `Event` objects are Pydantic models. Use `model_dump_json()` for SSE serialization:

```python
async def sse_event_generator():
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
        run_config=run_config
    ):
        event_json = event.model_dump_json(exclude_none=True, by_alias=True)
        yield f"data: {event_json}\n\n"
```

### FastAPI SSE Endpoint Example

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/chat/{user_id}")
async def chat_sse(user_id: str, message: str):
    new_message = types.Content(parts=[types.Part(text=message)])
    
    async def event_stream():
        async for event in runner.run_async(
            user_id=user_id,
            session_id=f"{user_id}-session",
            new_message=new_message,
            run_config=run_config
        ):
            event_json = event.model_dump_json(exclude_none=True, by_alias=True)
            yield f"data: {event_json}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

---

## Progressive SSE Streaming (Experimental)

An experimental feature that enhances SSE mode response aggregation:

- **Content ordering preservation**: Maintains order of mixed content types
- **Intelligent text merging**: Only merges consecutive text parts of same type
- **Deferred function execution**: Skips executing function calls in partial events

**Enable via environment variable:**

```bash
export ADK_ENABLE_PROGRESSIVE_SSE_STREAMING=1
```

Use when:

- Responses include thought text mixed with regular text
- Need better handling of mixed content types (text + function calls)
- Want to ensure function calls execute only once after complete aggregation

---

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `streaming_mode` | `StreamingMode` | `None` | Set to `StreamingMode.SSE` |
| `response_modalities` | `list[str]` | `None` | Use `["TEXT"]` for SSE mode |
| `max_llm_calls` | `int` | `None` | Limit total LLM calls per session |

---

## SSE vs BIDI Comparison

| Aspect | SSE Mode | BIDI Mode |
|--------|----------|-----------|
| **Protocol** | HTTP streaming | WebSocket |
| **API** | `generate_content_async()` | `live.connect()` |
| **Runner Method** | `run()` / `run_async()` | `run_live()` |
| **Communication** | Unidirectional (request → response) | Bidirectional (concurrent send/receive) |
| **Interruption** | Not supported | Supported |
| **Audio/Video** | Not supported | Supported |
| **Models** | Gemini 1.5 and 2.x | Gemini 2.x Live models only |
| **Turn Detection** | `finish_reason` | `turn_complete` flag |

---

## Supported Models

**Gemini 1.5 Series (SSE only):**

- `gemini-1.5-pro` - Up to 2M token context
- `gemini-1.5-flash` - Faster, lower latency

**Gemini 2.x Series (SSE and BIDI):**

- `gemini-2.0-flash` and variants

---

## Verification

```bash
# Run simple test
python -c "
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

agent = Agent(name='test', model='gemini-2.0-flash', instruction='Be helpful')
session_service = InMemorySessionService()
session_service.create_session(app_name='test', user_id='u1', session_id='s1')
runner = Runner(app_name='test', agent=agent, session_service=session_service)

config = RunConfig(streaming_mode=StreamingMode.SSE, response_modalities=['TEXT'])
msg = types.Content(parts=[types.Part(text='Hello')])

for event in runner.run(user_id='u1', session_id='s1', new_message=msg, run_config=config):
    if event.content and event.content.parts:
        print([p.text for p in event.content.parts if p.text])
"
```

Expected: Streaming text output from the agent.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No streaming events | Missing `streaming_mode` config | Set `streaming_mode=StreamingMode.SSE` |
| Model not supported | Using Live-only model with SSE | Use Gemini 1.5 or 2.x standard models |
| Function calls execute twice | Progressive SSE not enabled | Enable `ADK_ENABLE_PROGRESSIVE_SSE_STREAMING=1` |

---

## Related Workflows

- `/adk-streaming-bidi` - Bidirectional streaming with WebSocket and `run_live()`
- `/adk-behavior-events` - Understanding and handling ADK events
