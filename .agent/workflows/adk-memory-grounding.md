---
description: Enhance agents with long-term memory services and real-time grounding tools (google_search, Vertex AI Search, RAG)
---

# ADK Workflow: Memory and Grounding

Equip ADK agents with knowledge beyond their training data through **Memory Services** (long-term conversational knowledge) and **Grounding Tools** (real-time external data).

---

## Concepts Overview

ADK provides two complementary knowledge enhancement systems:

| System | Purpose | Data Source | Use Case |
|--------|---------|-------------|----------|
| **Memory Services** | Long-term knowledge from past conversations | Session history | "What did we discuss last week?" |
| **Grounding Tools** | Real-time external information | Web, enterprise docs, RAG corpora | "What's today's weather?" |

---

## Part A: Memory Services

Memory services enable agents to recall information from past conversations.

### Prerequisites

- [ ] ADK installed (`pip install google-adk`)
- [ ] For Vertex AI Memory Bank: Google Cloud project with Agent Engine

---

### Step 1: Choose a Memory Service

| Service | Persistence | Search | Use Case |
|---------|-------------|--------|----------|
| `InMemoryMemoryService` | None | Keyword | Prototyping, testing |
| `VertexAiMemoryBankService` | Yes | Semantic | Production with learning |

**In-Memory (Prototyping):**

```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()
```

**Vertex AI Memory Bank (Production):**

```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="YOUR_PROJECT_ID",
    location="us-central1",
    agent_engine_id="YOUR_AGENT_ENGINE_ID"
)
```

---

### Step 2: Configure Runner with Memory

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

runner = Runner(
    agent=your_agent,
    app_name="my_app",
    session_service=InMemorySessionService(),
    memory_service=memory_service  # Provide memory service
)
```

---

### Step 3: Add Memory Tools to Agent

ADK provides two built-in memory retrieval tools:

| Tool | Behavior | When to Use |
|------|----------|-------------|
| `PreloadMemoryTool` | Auto-loads memory every turn | Always have context available |
| `LoadMemoryTool` | Agent decides when to search | Selective memory access |

**PreloadMemory (Automatic):**

```python
from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

agent = Agent(
    model="gemini-2.0-flash",
    name="memory_agent",
    instruction="Answer questions using past conversation context.",
    tools=[PreloadMemoryTool()]
)
```

**LoadMemory (On-Demand):**

```python
from google.adk.agents import Agent
from google.adk.tools import load_memory

agent = Agent(
    model="gemini-2.0-flash",
    name="memory_agent",
    instruction="Use load_memory to search past conversations when relevant.",
    tools=[load_memory]
)
```

---

### Step 4: Save Sessions to Memory

Call `add_session_to_memory` after completing a session:

```python
# After conversation ends
completed_session = await session_service.get_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=session_id
)
await memory_service.add_session_to_memory(completed_session)
```

**Auto-save via callback:**

```python
async def auto_save_callback(callback_context):
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )

agent = Agent(
    model="gemini-2.0-flash",
    name="auto_memory_agent",
    instruction="...",
    tools=[PreloadMemoryTool()],
    after_agent_callback=auto_save_callback
)
```

---

## Part B: Grounding Tools

Grounding tools connect agents to real-time external information.

### Tool Comparison

| Tool | Data Source | Platform | Limitation |
|------|-------------|----------|------------|
| `google_search` | Web (Google Search) | AI Studio or Vertex AI | Gemini 2+ only |
| `VertexAiSearchTool` | Enterprise documents | Vertex AI only | Requires datastore setup |
| `VertexAiRagRetrieval` | RAG corpus | Vertex AI only | Single-tool agent only |

---

### Option 1: Google Search Grounding

Ground responses with real-time web data.

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    instruction="Answer questions using Google Search. Always cite sources.",
    tools=[google_search]
)
```

**Grounding metadata** is returned with sources:

```python
for event in events:
    if event.is_final_response():
        print(event.content.parts[0].text)
        if event.grounding_metadata:
            for chunk in event.grounding_metadata.grounding_chunks:
                print(f"Source: {chunk.web.title} - {chunk.web.uri}")
```

---

### Option 2: Vertex AI Search (Enterprise Documents)

Ground responses with indexed enterprise documents.

**Prerequisites:**
- Vertex AI Search datastore with indexed documents
- `GOOGLE_GENAI_USE_VERTEXAI=TRUE` in `.env`

```python
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool

DATASTORE_ID = "projects/PROJECT/locations/global/collections/default_collection/dataStores/DATASTORE_ID"

agent = Agent(
    name="enterprise_search_agent",
    model="gemini-2.5-flash",
    instruction="Answer questions from company documents. Cite sources.",
    tools=[VertexAiSearchTool(data_store_id=DATASTORE_ID)]
)
```

---

### Option 3: Vertex AI RAG Engine

Ground responses with a custom RAG corpus.

> [!WARNING]
> `VertexAiRagRetrieval` can only be used **by itself** within an agent—no other tools allowed.

**Prerequisites:**
- Vertex AI RAG corpus prepared
- `GOOGLE_GENAI_USE_VERTEXAI=TRUE` in `.env`

```python
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

rag_tool = VertexAiRagRetrieval(
    name="retrieve_docs",
    description="Retrieve documentation from RAG corpus",
    rag_resources=[
        rag.RagResource(
            rag_corpus="projects/PROJECT_ID/locations/LOCATION/ragCorpora/CORPUS_ID"
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6
)

agent = Agent(
    model="gemini-2.0-flash",
    name="rag_agent",
    instruction="Answer questions using retrieved documents.",
    tools=[rag_tool]  # Must be the ONLY tool
)
```

---

## Configuration Options

### VertexAiRagRetrieval Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Tool name |
| `description` | `str` | Tool description for the model |
| `rag_corpora` | `list[str]` | List of RAG corpus resource names |
| `rag_resources` | `list[RagResource]` | RAG resource configurations |
| `similarity_top_k` | `int` | Number of top results to return |
| `vector_distance_threshold` | `float` | Minimum similarity threshold |

### VertexAiSearchTool Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_store_id` | `str` | Full resource path to Vertex AI Search datastore |

---

## Integration Patterns

### Memory + Grounding Combined

Use memory for conversational context and grounding for real-time data:

```python
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

agent = Agent(
    model="gemini-2.5-flash",
    name="informed_agent",
    instruction="""
    Answer questions using:
    1. Past conversation context (automatically loaded)
    2. Google Search for current information
    Always cite sources.
    """,
    tools=[PreloadMemoryTool(), google_search]
)
```

---

## Verification

### Test Memory

```bash
adk web path/to/agent --memory_service_uri="agentengine://YOUR_ENGINE_ID"
```

1. Session 1: "My favorite color is blue."
2. Session 2: "What's my favorite color?" → Should recall "blue"

### Test Grounding

```bash
adk run google_search_agent
```

Ask time-sensitive questions:
- "What's the weather in Tokyo?"
- "What's the current stock price of Google?"

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Memory not found | Session not saved | Call `add_session_to_memory()` |
| `google_search` fails | Wrong model | Use Gemini 2+ models |
| RAG returns no results | Threshold too high | Lower `vector_distance_threshold` |
| VertexAiSearchTool error | Wrong datastore path | Use full resource path format |

---

## References

- Memory documentation: `docs/sessions/memory.md`
- Google Search grounding: `docs/grounding/google_search_grounding.md`
- Vertex AI Search grounding: `docs/grounding/vertex_ai_search_grounding.md`
- Vertex AI RAG Engine: `docs/tools/google-cloud/vertex-ai-rag-engine.md`
- PreloadMemoryTool: `src/google/adk/tools/preload_memory_tool.py`
- VertexAiRagRetrieval: `src/google/adk/tools/retrieval/vertex_ai_rag_retrieval.py`
