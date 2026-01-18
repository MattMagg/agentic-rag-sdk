---
description: Configure memory services for long-term knowledge persistence and retrieval in ADK agents
---

# ADK Workflow: Memory Service Configuration

Configure `MemoryService` implementations to provide agents with long-term knowledge storage and retrieval capabilities across sessions.

---

## Prerequisites

- [ ] ADK installed (`pip install google-adk`)
- [ ] For `VertexAiMemoryBankService`: Google Cloud project with Vertex AI API enabled
- [ ] For `VertexAiRagMemoryService`: Vertex AI RAG corpus created

---

## Step 1: Choose Memory Service Implementation

ADK provides three `MemoryService` implementations:

| Service | Storage | Search | Use Case |
|---------|---------|--------|----------|
| `InMemoryMemoryService` | In-process memory | Keyword matching | Prototyping, testing |
| `VertexAiMemoryBankService` | Vertex AI Memory Bank | Semantic search | Production with intelligent memory extraction |
| `VertexAiRagMemoryService` | Vertex AI RAG Corpus | Semantic search | Production with RAG-based retrieval |

---

## Step 2: Configure Memory Service

### Option A: InMemoryMemoryService (Default)

Best for prototyping. No persistence - data lost on restart.

```python
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

memory_service = InMemoryMemoryService()

runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service,
    memory_service=memory_service
)
```

### Option B: VertexAiMemoryBankService

Production service with intelligent memory extraction and semantic search.

**Prerequisites:**
```bash
# Authenticate
gcloud auth application-default login

# Set environment variables
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

**CLI Configuration:**
```bash
adk web path/to/agents --memory_service_uri="agentengine://<agent_engine_id>"
```

**Programmatic Configuration:**
```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="your-project-id",
    location="us-central1",
    agent_engine_id="your-agent-engine-id"  # Just the ID, not the full path
)
```

### Option C: VertexAiRagMemoryService

Uses Vertex AI RAG corpus for storage and retrieval.

**CLI Configuration:**
```bash
adk web path/to/agents --memory_service_uri="rag://<rag_corpus_id>"
```

**Programmatic Configuration:**
```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/{project}/locations/{location}/ragCorpora/{corpus_id}",
    similarity_top_k=10,
    vector_distance_threshold=10.0
)
```

---

## Step 3: Add Memory Tools to Agent

ADK provides two built-in memory retrieval tools:

### PreloadMemoryTool (Automatic)

Automatically retrieves relevant memories at the start of each turn.

```python
from google.adk.agents import LlmAgent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="MemoryAgent",
    instruction="Answer questions using past conversation context.",
    tools=[PreloadMemoryTool()]
)
```

### LoadMemoryTool (On-Demand)

Agent decides when to retrieve memories based on user query.

```python
from google.adk.agents import LlmAgent
from google.adk.tools import load_memory

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="MemoryAgent",
    instruction="Use load_memory tool when past context is needed.",
    tools=[load_memory]
)
```

---

## Step 4: Ingest Sessions into Memory

Sessions must be explicitly added to memory after completion:

### Manual Ingestion

```python
# After session completes
completed_session = await session_service.get_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=session_id
)
await memory_service.add_session_to_memory(completed_session)
```

### Automatic Ingestion via Callback

```python
from google.adk.agents import LlmAgent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

async def auto_save_memory(callback_context):
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="AutoMemoryAgent",
    instruction="Answer questions.",
    tools=[PreloadMemoryTool()],
    after_agent_callback=auto_save_memory
)
```

---

## Step 5: Search Memory Programmatically

Access memory from within custom tools using `ToolContext`:

```python
from google.adk.tools import ToolContext

async def my_custom_tool(query: str, tool_context: ToolContext) -> str:
    # Search memory using configured service
    response = await tool_context.search_memory(query)
    
    for memory in response.memories:
        print(f"{memory.author}: {memory.content}")
    
    return f"Found {len(response.memories)} relevant memories"
```

---

## Configuration Options

### VertexAiMemoryBankService Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project` | `str` | Yes | Google Cloud project ID |
| `location` | `str` | Yes | GCP location (e.g., `us-central1`) |
| `agent_engine_id` | `str` | Yes | Agent Engine ID (just the ID, not full path) |
| `express_mode_api_key` | `str` | No | API key for Express Mode |

### VertexAiRagMemoryService Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rag_corpus` | `str` | None | Full RAG corpus path or just corpus ID |
| `similarity_top_k` | `int` | None | Number of contexts to retrieve |
| `vector_distance_threshold` | `float` | 10.0 | Max vector distance for results |

### CLI Memory Service URI Formats

| Format | Service |
|--------|---------|
| (none) | `InMemoryMemoryService` (default) |
| `agentengine://<id>` | `VertexAiMemoryBankService` |
| `rag://<corpus_id>` | `VertexAiRagMemoryService` |

---

## Advanced: Multiple Memory Services

Use multiple memory sources within a single agent:

```python
from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService

class MultiMemoryAgent(LlmAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary memory for conversation history
        self.conversation_memory = InMemoryMemoryService()
        
        # Secondary memory for knowledge base
        self.knowledge_memory = VertexAiMemoryBankService(
            project="project-id",
            location="us-central1",
            agent_engine_id="engine-id"
        )
    
    async def search_both_memories(self, query: str):
        conv_results = await self.conversation_memory.search_memory(
            app_name="app", user_id="user", query=query
        )
        knowledge_results = await self.knowledge_memory.search_memory(
            app_name="app", user_id="user", query=query
        )
        return conv_results, knowledge_results
```

---

## Verification

```bash
# Run agent with memory service
adk run my_agent_folder

# Or with explicit memory configuration
adk web my_agent_folder --memory_service_uri="agentengine://12345"
```

**Expected behavior:**
1. Agent can store session information via `add_session_to_memory`
2. Agent can retrieve relevant context via `search_memory`
3. Memory persists across sessions (except `InMemoryMemoryService`)

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `ValueError: Agent Engine ID is required` | Missing agent_engine_id | Provide `agent_engine_id` or use `--memory_service_uri` |
| Memory not persisting | Using `InMemoryMemoryService` | Switch to `VertexAiMemoryBankService` for persistence |
| No memories returned | Sessions not added to memory | Call `add_session_to_memory()` after session ends |
| `ImportError: vertexai` | Missing Vertex AI SDK | `pip install google-cloud-aiplatform` |
| Full path warning in logs | `agent_engine_id` includes `/` | Extract just the ID: `name.split('/')[-1]` |

---

## References

- ADK Memory Documentation: `docs/sessions/memory.md`
- BaseMemoryService Interface: `google.adk.memory.BaseMemoryService`
- Memory Tools: `google.adk.tools.load_memory`, `google.adk.tools.preload_memory`
- Vertex AI Memory Bank: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview
