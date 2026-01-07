---
description: Implement audio, image, and video I/O in ADK bidi-streaming (live) agents
---

# ADK Workflow: Streaming Multimodal

Build live streaming agents that handle real-time **audio**, **image**, and **video** input/output via the Live API.

---

## Prerequisites

- [ ] ADK Python v0.5.0+
- [ ] Import core types:

```python
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
```

---

## Step 1: Configure BIDI Streaming Mode

Enable bidirectional WebSocket streaming via `StreamingMode.BIDI`:

```python
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"]  # Or ["TEXT"] for text-only responses
)
```

> [!IMPORTANT]
> Only ONE response modality per session. Cannot switch mid-session.

---

## Step 2: Send Audio Input

**Audio Format Requirements (Input):**
- **Format**: 16-bit PCM (signed integer)
- **Sample Rate**: 16,000 Hz (16kHz)
- **Channels**: Mono

```python
# Create audio blob with correct format
audio_blob = types.Blob(
    mime_type="audio/pcm;rate=16000",
    data=audio_data  # Raw PCM bytes
)
live_request_queue.send_realtime(audio_blob)
```

**Best Practices:**
- Send in 50-100ms chunks (~1600-3200 bytes @ 16kHz) for balanced latency
- Stream continuously—the model processes audio without turn-by-turn waits
- Automatic VAD (Voice Activity Detection) is enabled by default

---

## Step 3: Receive Audio Output

**Audio Format (Output):**
- **Format**: 16-bit PCM
- **Sample Rate**: 24,000 Hz (24kHz)
- **Channels**: Mono

```python
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_request_queue,
    run_config=RunConfig(
        response_modalities=["AUDIO"],
        streaming_mode=StreamingMode.BIDI
    )
):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                audio_bytes = part.inline_data.data  # 24kHz, 16-bit PCM
                await stream_audio_to_client(audio_bytes)
```

---

## Step 4: Send Image and Video

Images and video frames are sent as JPEG:

**Specifications:**
- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 FPS recommended maximum
- **Resolution**: 768x768 pixels recommended

```python
import base64

# Decode base64 image data
image_data = base64.b64decode(base64_image_string)

# Send as blob
image_blob = types.Blob(
    mime_type="image/jpeg",
    data=image_data
)
live_request_queue.send_realtime(image_blob)
```

> [!NOTE]
> Video is processed as sequential JPEG frames, not streaming formats like HLS or mp4.

---

## Step 5: Configure Audio Transcription

Enable text transcription of audio (for captions, logging):

```python
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI,
    input_audio_transcription=types.AudioTranscriptionConfig(),   # User speech → text  
    output_audio_transcription=types.AudioTranscriptionConfig()   # Model speech → text
)
```

Access transcriptions from events:

```python
async for event in runner.run_live(...):
    if event.input_transcription:
        print(f"User said: {event.input_transcription.text}")
    if event.output_transcription:
        print(f"Model said: {event.output_transcription.text}")
```

---

## Step 6: Voice Configuration

Configure voice for audio output:

```python
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr
            )
        )
    )
)
```

---

## Step 7: Implement Streaming Tools (Video Processing)

Create tools that process video frames in real-time:

```python
from typing import AsyncGenerator
from google.adk.agents import LiveRequestQueue
from google.adk.tools.function_tool import FunctionTool

# Video streaming tool - receives video frames via input_stream
async def monitor_video_stream(
    input_stream: LiveRequestQueue,
) -> AsyncGenerator[str, None]:
    """Monitor the video stream for changes."""
    while True:
        # Pull latest frame from queue
        while input_stream._queue.qsize() != 0:
            live_req = await input_stream.get()
            if live_req.blob and live_req.blob.mime_type == "image/jpeg":
                # Process frame...
                yield "Detected change in video"
        await asyncio.sleep(0.5)

# Required: stop function for ADK to terminate streaming tools
def stop_streaming(function_name: str):
    """Stop the streaming function."""
    pass

agent = Agent(
    model="gemini-3-flash-preview-native-audio-preview-09-2025",
    name="video_agent",
    instruction="Monitor video streams using provided tools.",
    tools=[monitor_video_stream, FunctionTool(stop_streaming)]
)
```

---

## Audio Model Architectures

| Architecture | Description | Models |
|--------------|-------------|--------|
| **Native Audio** | End-to-end audio processing, natural prosody | `gemini-3-flash-preview-native-audio-preview-09-2025` |
| **Half-Cascade** | Audio input + TTS output, more reliable tool execution | `gemini-3-flash-preview-live-001` |

**Use Native Audio for**: Natural conversations, advanced features (affective dialog, proactivity)  
**Use Half-Cascade for**: Production reliability with tool execution

---

## Configuration Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_modalities` | list[str] | `["AUDIO"]` or `["TEXT"]` - one per session |
| `streaming_mode` | StreamingMode | `BIDI` for live streaming, `SSE` for text-only |
| `speech_config` | SpeechConfig | Voice selection and language |
| `input_audio_transcription` | AudioTranscriptionConfig | Transcribe user audio to text |
| `output_audio_transcription` | AudioTranscriptionConfig | Transcribe model audio to text |
| `session_resumption` | SessionResumptionConfig | Enable automatic reconnection |
| `context_window_compression` | ContextWindowCompressionConfig | Unlimited session duration |

---

## Complete Example

```python
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create agent
agent = Agent(
    model="gemini-3-flash-preview-native-audio-preview-09-2025",
    name="voice_agent",
    instruction="You are a helpful voice assistant."
)

# Setup runner
session_service = InMemorySessionService()
runner = Runner(agent=agent, session_service=session_service, app_name="voice_app")

# Create session
session = await session_service.create_session(
    app_name="voice_app",
    user_id="user_123",
    session_id="session_456"
)

# Configure streaming
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],
    session_resumption=types.SessionResumptionConfig(),
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    )
)

# Create request queue
live_request_queue = LiveRequestQueue()

# Process events
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_request_queue,
    run_config=run_config
):
    # Handle audio output
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                await stream_audio_to_client(part.inline_data.data)
```

---

## Verification

```bash
adk web agent_folder  # Opens browser with audio/video interface
```

**Expected behavior:**
- Microphone captures audio → sent to model
- Model responds with audio playback
- Camera captures video frames → processed by model

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No audio output | Wrong `response_modalities` | Set to `["AUDIO"]` |
| Garbled audio | Wrong sample rate | Input: 16kHz, Output: 24kHz |
| Video not processed | Wrong format | Use JPEG at 1 FPS, 768x768 |
| Session timeout | No resumption config | Enable `session_resumption` |
| Model ignores | Disabled VAD + no signals | Send `send_activity_start/end` or enable VAD |

---

## References

- [docs/streaming/dev-guide/part2.md](file:///Users/mac-main/rag_qdrant_voyage/corpora/adk-docs/docs/streaming/dev-guide/part2.md) - LiveRequestQueue
- [docs/streaming/dev-guide/part4.md](file:///Users/mac-main/rag_qdrant_voyage/corpora/adk-docs/docs/streaming/dev-guide/part4.md) - RunConfig
- [docs/streaming/dev-guide/part5.md](file:///Users/mac-main/rag_qdrant_voyage/corpora/adk-docs/docs/streaming/dev-guide/part5.md) - Audio/Image/Video
- [docs/streaming/streaming-tools.md](file:///Users/mac-main/rag_qdrant_voyage/corpora/adk-docs/docs/streaming/streaming-tools.md) - Streaming Tools
