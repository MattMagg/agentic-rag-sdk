---
description: Enable bidirectional streaming with WebSocket and run_live() for real-time audio/video ADK agents
---

# ADK Workflow: BIDI Streaming

Configure ADK agents for bidirectional streaming using WebSocket connections to the Live API, enabling real-time audio/video interactions with concurrent send/receive capabilities.

---

## When to Use BIDI Mode

Use `StreamingMode.BIDI` when:

- Building voice/video applications with real-time interaction
- Need bidirectional communication (send while receiving)
- Require Live API features (audio transcription, VAD, proactivity, affective dialog)
- Supporting interruptions and natural turn-taking
- Implementing live streaming tools or real-time data feeds
- Can plan for concurrent session quotas (50-1,000 sessions depending on platform/tier)

**Use SSE instead when:**

- Building text-based chat applications
- Standard request/response interaction pattern
- Using Gemini 1.5 models (no Live API support)

---

## Prerequisites

- [ ] ADK installed with streaming support
- [ ] Gemini 2.x Live model (e.g., `gemini-2.5-flash-native-audio-preview-09-2025`)
- [ ] WebSocket server framework (e.g., FastAPI)

```python
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
```

---

## Step 1: Configure StreamingMode.BIDI

BIDI mode uses WebSocket to connect to the Live API via `live.connect()`.

```python
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],  # For voice apps, or ["TEXT"] for text
    # Enable audio transcription for accessibility
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    # Enable session resumption for long sessions
    session_resumption=types.SessionResumptionConfig()
)
```

---

## Step 2: Create LiveRequestQueue

`LiveRequestQueue` is the communication channel for sending messages to the agent during streaming.

```python
from google.adk.agents.live_request_queue import LiveRequestQueue

# Create queue for this session (session-specific, cannot be reused)
live_request_queue = LiveRequestQueue()
```

> **Important**: Create a new `LiveRequestQueue` for each streaming session. Never reuse queues across sessions.

---

## Step 3: Start run_live() Event Loop

Use the `run_live()` async generator to process events bidirectionally.

```python
async for event in runner.run_live(
    user_id=user_id,
    session_id=session_id,
    live_request_queue=live_request_queue,
    run_config=run_config
):
    # Process each event as it arrives
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                # Handle text response
                await websocket.send_text(part.text)
            if hasattr(part, 'inline_data') and part.inline_data:
                # Handle audio/video blob
                await websocket.send_bytes(part.inline_data.data)
```

---

## Step 4: Send Messages via LiveRequestQueue

While `run_live()` is running, send messages concurrently through the queue.

### Send Text Content

```python
content = types.Content(parts=[types.Part(text="Hello, how are you?")])
live_request_queue.send_content(content)
```

### Send Audio/Video Blobs

```python
# Audio: 16-bit PCM at 16kHz mono
audio_blob = types.Blob(
    mime_type="audio/pcm;rate=16000",
    data=audio_bytes
)
live_request_queue.send_realtime(audio_blob)

# Image
image_blob = types.Blob(
    mime_type="image/jpeg",
    data=image_bytes
)
live_request_queue.send_realtime(image_blob)

# Video frame (1 fps recommended)
video_blob = types.Blob(
    mime_type="image/jpeg",  # Video frames sent as images
    data=frame_bytes
)
live_request_queue.send_realtime(video_blob)
```

### Close the Queue

Always close the queue when the session ends:

```python
live_request_queue.close()
```

---

## Step 5: Complete FastAPI WebSocket Example

```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.sessions import InMemorySessionService
from google.adk.agents import Agent
from google.genai import types

# Phase 1: Application Initialization (once at startup)
APP_NAME = "bidi-app"
app = FastAPI()

agent = Agent(
    name="voice_assistant",
    model="gemini-2.5-flash-native-audio-preview-09-2025",
    instruction="You are a helpful voice assistant."
)
session_service = InMemorySessionService()
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()

    # Phase 2: Session Initialization
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        session_resumption=types.SessionResumptionConfig()
    )

    # Get or create session
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    live_request_queue = LiveRequestQueue()

    # Phase 3: Bidi-streaming with concurrent tasks
    async def upstream_task():
        """Receives from WebSocket, sends to LiveRequestQueue."""
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    audio_blob = types.Blob(
                        mime_type="audio/pcm;rate=16000",
                        data=message["bytes"]
                    )
                    live_request_queue.send_realtime(audio_blob)
                elif "text" in message:
                    content = types.Content(
                        parts=[types.Part(text=message["text"])]
                    )
                    live_request_queue.send_content(content)
        except WebSocketDisconnect:
            pass

    async def downstream_task():
        """Receives from run_live(), sends to WebSocket."""
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            event_json = event.model_dump_json(exclude_none=True, by_alias=True)
            await websocket.send_text(event_json)

    try:
        await asyncio.gather(upstream_task(), downstream_task())
    finally:
        # Phase 4: Terminate
        live_request_queue.close()
```

---

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `streaming_mode` | `StreamingMode` | `None` | Set to `StreamingMode.BIDI` |
| `response_modalities` | `list[str]` | `["AUDIO"]` | `["AUDIO"]` or `["TEXT"]` (only one allowed per session) |
| `session_resumption` | `SessionResumptionConfig` | `None` | Enable automatic reconnection for long sessions |
| `context_window_compression` | `ContextWindowCompressionConfig` | `None` | Enable unlimited session duration |
| `input_audio_transcription` | `AudioTranscriptionConfig` | `None` | Transcribe user speech |
| `output_audio_transcription` | `AudioTranscriptionConfig` | `None` | Transcribe model speech |

### Session Resumption

Handles Gemini's ~10 minute connection timeouts transparently:

```python
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    session_resumption=types.SessionResumptionConfig()
)
```

### Context Window Compression

Enable unlimited session duration:

```python
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100000,  # Start compression at ~78% of 128k
        sliding_window=types.SlidingWindow(target_tokens=80000)
    )
)
```

---

## Platform Limits

| Constraint | Gemini Live API | Vertex AI Live API |
|------------|-----------------|-------------------|
| **Session Duration (Audio)** | 15 min (unlimited with compression) | 10 min (unlimited with compression) |
| **Session Duration (Audio+Video)** | 2 min (unlimited with compression) | 10 min (unlimited with compression) |
| **Concurrent Sessions** | 50 (Tier 1) to 1,000 (Tier 2+) | Up to 1,000 per project |
| **Connection Timeout** | ~10 min (auto-reconnect with resumption) | Not documented separately |

---

## Event Types

Key events from `run_live()`:

| Event Indicator | Description |
|-----------------|-------------|
| `event.content.parts[].text` | Text response chunk |
| `event.content.parts[].inline_data` | Audio/video blob |
| `event.actions.state_delta` | State changes |
| `event.turn_complete` | Model finished current turn |
| `event.interrupted` | User interrupted the response |
| `event.error` | Error occurred |

---

## Verification

```bash
# Install dependencies
pip install fastapi uvicorn websockets

# Run the server
uvicorn main:app --reload

# Test with WebSocket client
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws/user1/session1') as ws:
        await ws.send('Hello!')
        response = await ws.recv()
        print(f'Received: {response}')

asyncio.run(test())
"
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Session not found` | Session not created before `run_live()` | Call `create_session()` first |
| Connection drops after 10 min | Session resumption not enabled | Add `session_resumption=types.SessionResumptionConfig()` |
| No audio output | Wrong response modality | Set `response_modalities=["AUDIO"]` |
| Queue reuse error | Reusing closed queue | Create new `LiveRequestQueue` per session |
| Messages not processed | Queue created in wrong thread | Create queue in async context |

---

## Four-Phase Lifecycle Summary

1. **Phase 1: Application Init** - Create Agent, SessionService, Runner (once at startup)
2. **Phase 2: Session Init** - Create RunConfig, get/create Session, create LiveRequestQueue (per user connection)
3. **Phase 3: Bidi-streaming** - Concurrent upstream (user→queue) and downstream (run_live→user) tasks
4. **Phase 4: Terminate** - `live_request_queue.close()` (on disconnect or completion)

---

## Related Workflows

- `/adk-streaming-sse` - SSE streaming for text-based agents
- `/adk-behavior-events` - Understanding and handling ADK events
- `/adk-behavior-state` - Managing session state
