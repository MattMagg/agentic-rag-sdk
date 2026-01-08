---
name: ADK Streaming
description: This skill should be used when the user asks about "streaming", "real-time responses", "SSE", "server-sent events", "websocket", "bidirectional", "Live API", "voice", "audio", "video", "multimodal streaming", or needs guidance on implementing real-time communication between agents and clients.
version: 2.0.0
---

# ADK Streaming

Guide for implementing streaming and real-time communication in ADK agents. Enables text streaming, bidirectional chat, and voice/video interactions.

## When to Use

- Streaming text responses as they generate
- Real-time chat with user interrupts
- Voice agent interactions (Live API)
- Video processing and multimodal streaming
- WebSocket bidirectional communication

## When NOT to Use

- Standard request/response → Use `@adk-agents` instead
- Agent deployment → Use `@adk-deployment` instead
- Tool integration → Use `@adk-tools` instead

## Key Concepts

**SSE (Server-Sent Events)** streams text responses incrementally. Client receives partial responses as they generate.

**Bidirectional Streaming** enables real-time two-way communication. Users can interrupt agent responses mid-stream.

**Live API** powers voice and video agents. Use `gemini-3-flash-live` model for real-time audio/video processing.

**Runner Types**: `Runner` for basic execution, `BidiStreamingRunner` for bidirectional, `LiveAPIRunner` for voice/video.

## References

Detailed guides with code examples:
- `references/sse.md` - Server-sent events streaming
- `references/bidirectional.md` - WebSocket bidirectional
- `references/multimodal.md` - Live API voice/video
