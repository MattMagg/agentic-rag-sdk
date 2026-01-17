# ADK Development Workflow Table of Contents

> **Purpose**: Hierarchical guide for IDE coding agents to autonomously build agentic systems using Google ADK and Vertex AI.
> 
> **Source**: Identified from RAG retrieval of `adk-docs` and `adk-python` corpora.

---

## Level 1: Foundation

### Workflow: Project Initialization
> Scope: Bootstrap a new ADK project with proper structure and dependencies.

#### Sections:
1. **Project Creation** — Use `adk create` CLI to scaffold project
   - Directory structure conventions (`agent.py`, `__init__.py`)
   - Requirements and dependency management
2. **Environment Configuration** — API keys and model access
   - Google Cloud project setup
   - `GOOGLE_API_KEY` vs service account authentication
   - Vertex AI Gemini model configuration
3. **Local Development** — Running agents locally
   - `adk web` for interactive dev UI
   - `adk run` for CLI execution

---

### Workflow: Basic Agent Creation
> Scope: Create a minimal LlmAgent with model, name, and instructions.

#### Sections:
1. **LlmAgent Constructor** — Core agent instantiation
   - `name`, `model`, `instruction` parameters
   - Model selection (`gemini-2.5-pro`, `gemini-2.0-flash`, etc.)
2. **System Instructions** — Defining agent behavior
   - Static instruction strings
   - Dynamic instruction callbacks
3. **Agent Description** — For multi-agent routing
   - Purpose of `description` field
   - Best practices for agent discovery

---

### Workflow: Multi-Model Support
> Scope: Use non-Gemini models (Claude, GPT, etc.) via LiteLLM or direct integrations.

#### Sections:
1. **LiteLLM Integration** — Universal model wrapper
   - Installing and configuring LiteLLM
   - OpenAI, Anthropic, Cohere model access
2. **Anthropic Claude on Vertex AI** — Direct integration
   - `Claude` class configuration
   - Vertex AI model garden access
3. **API Key Management** — Provider authentication
   - Environment variable patterns
   - Credential injection

---

### Workflow: YAML Declarative Configuration
> Scope: Define agents using YAML configuration files instead of Python code.

#### Sections:
1. **Agent Config Files** — YAML-based agent definition
   - `root_agent.yaml` file structure
   - JSON schema validation
2. **Config Loading** — Building agents from config
   - `from_config()` utility function
   - `adk create --type=config` scaffolding
3. **LlmAgentConfig Schema** — Available configuration options
   - Model, instruction, tools specification
   - Sub-agent configuration in YAML

---

## Level 2: Tools & Capabilities

### Workflow: Adding Function Tools
> Scope: Extend agent capabilities with custom Python functions.

#### Sections:
1. **FunctionTool Basics** — Convert functions to tools
   - Automatic schema generation from type hints
   - Docstring-based descriptions
2. **ToolContext Integration** — Access runtime context
   - State reading/writing via `tool_context.state`
   - Agent flow control via `tool_context.actions`
3. **Tool Registration** — Adding tools to agents
   - Direct tool list assignment
   - Conditional tool availability

---

### Workflow: Long-Running Function Tools
> Scope: Handle async operations that require background processing or human approval.

#### Sections:
1. **LongRunningFunctionTool** — Async tool pattern
   - Returning pending status to agent
   - Ticket-based result tracking
2. **Intermediate Updates** — Progress reporting
   - Sending intermediate results
   - Final result submission
3. **Human-in-the-Loop** — Manual approval flows
   - Pausing for human decision
   - Resuming with human input

---

### Workflow: Built-in Tool Integration
> Scope: Leverage ADK's pre-built tools (search, code execution).

#### Sections:
1. **Google Search Tool** — Web grounding capabilities
   - `google_search` import and usage
   - `GoogleSearchAgentTool` for multi-tool compatibility
2. **Code Execution** — Sandboxed code running
   - `code_execution` tool configuration
   - Security considerations
3. **Google Cloud Tools** — Enterprise integrations
   - Application Integration tools
   - BigQuery, Spanner connectors

---

### Workflow: OpenAPI Tool Integration
> Scope: Automatically generate tools from REST API specifications.

#### Sections:
1. **OpenAPIToolset** — Parse specs into tools
   - Loading from JSON/YAML files
   - Fetching from URLs
2. **RestApiTool** — Individual API operation tools
   - Request parameter generation
   - Response handling
3. **Authentication Attachment** — Secure API calls
   - Auth scheme configuration
   - Credential injection per tool

---

### Workflow: MCP Tool Integration
> Scope: Connect agents to external systems via Model Context Protocol.

#### Sections:
1. **McpToolset Configuration** — Server connection setup
   - Stdio transport (subprocess-based)
   - SSE transport (HTTP-based)
2. **Tool Discovery** — Auto-loading MCP tools
   - `McpToolset` tool list injection
   - Tool filtering and selection
3. **Bidirectional Integration** — Exposing ADK as MCP server
   - ADK-to-MCP tool conversion
   - MCP server implementation patterns

---

### Workflow: Third-Party Tool Adapters
> Scope: Integrate tools from external AI frameworks (LangChain, CrewAI).

#### Sections:
1. **LangchainTool Adapter** — Wrap LangChain tools for ADK
   - `LangchainTool` class usage
   - Schema conversion and execution
2. **CrewaiTool Adapter** — Wrap CrewAI tools for ADK
   - `CrewaiTool` class usage
   - Tool name and description overrides
3. **Integration Patterns** — Best practices
   - Dependency management
   - Error handling across frameworks

---

### Workflow: Computer Use Automation
> Scope: Enable agents to control desktop and browser environments.

#### Sections:
1. **ComputerUseToolset** — Desktop automation setup
   - `BaseComputer` implementation
   - Screen capture and coordinate normalization
2. **Computer Actions** — Available operations
   - Click, type, scroll, screenshot
   - Keyboard shortcuts and drag operations
3. **Browser Automation** — Web interaction patterns
   - Navigation and form filling
   - Security sandboxing considerations

---

## Level 3: Agent Behavior & Lifecycle

### Workflow: Implementing Callbacks
> Scope: Intercept and customize agent execution at key lifecycle points.

#### Sections:
1. **Agent Callbacks** — Before/after agent execution
   - `before_agent_callback` for preprocessing
   - `after_agent_callback` for postprocessing
2. **Model Callbacks** — LLM request/response interception
   - `before_model_callback` for prompt modification
   - `after_model_callback` for response filtering
3. **Tool Callbacks** — Tool execution control
   - `before_tool_callback` for validation/modification
   - `after_tool_callback` for result processing
4. **Confirmation Callbacks** — Basic approval patterns
   - `request_confirmation` in ToolContext
   - Confirmation callback patterns

---

### Workflow: Tool Confirmation Flows
> Scope: Implement human approval workflows for sensitive tool actions.

#### Sections:
1. **require_confirmation Flag** — Automatic confirmation
   - `FunctionTool(require_confirmation=True)`
   - Conditional confirmation with functions
2. **Manual Confirmation** — Programmatic control
   - `tool_context.request_confirmation()` method
   - Custom confirmation messages
3. **Remote Confirmation** — External approval
   - REST API confirmation patterns
   - Command-line confirmation interface
4. **Confirmation UI** — User-facing flows
   - `adk web` confirmation handling
   - Custom UI integration patterns

---

### Workflow: Plugins System
> Scope: Reusable, composable extensions for cross-cutting concerns.

#### Sections:
1. **BasePlugin Architecture** — Plugin structure
   - Callback method overrides
   - Runner registration
2. **Built-in Plugins** — Ready-to-use plugins
   - `SaveFilesAsArtifactsPlugin` for file handling
   - `SecurityPlugin` for access control
3. **Custom Plugin Development** — Building reusable components
   - Lifecycle hook implementation
   - State isolation between plugins

---

### Workflow: State Management
> Scope: Persist and share data across agent interactions.

#### Sections:
1. **Session State** — Per-session scratchpad
   - Reading state via context objects
   - Writing state with automatic persistence
2. **State Prefixes** — Scoping state access
   - `app:` prefix for global state
   - `user:` prefix for user-specific state
   - `temp:` prefix for volatile state
3. **SessionService Implementations** — Storage backends
   - `InMemorySessionService` for prototyping
   - `DatabaseSessionService` for production

---

### Workflow: Artifact Management
> Scope: Handle file uploads, downloads, and binary data.

#### Sections:
1. **ArtifactService Setup** — Configuring storage
   - `InMemoryArtifactService` for development
   - `GcsArtifactService` for production
2. **Saving Artifacts** — Storing files from tools
   - `tool_context.save_artifact()` method
   - Metadata and versioning
3. **Loading Artifacts** — Retrieving stored files
   - `tool_context.load_artifact()` method
   - Artifact listing and search

---

### Workflow: Events & EventActions
> Scope: Understand and control agent execution flow via the event stream.

#### Sections:
1. **Event Model** — Immutable execution records
   - Event structure (`author`, `content`, `actions`)
   - Event types (user, agent, tool, system)
2. **EventActions** — Flow control mechanisms
   - `transfer_to_agent` for delegation
   - `escalate` for loop exit
   - `skip_summarization` for performance
3. **Event Iteration** — Processing agent output
   - Async generator patterns
   - Filtering by event type

---

### Workflow: Custom Agent Implementation
> Scope: Build specialized agents by extending BaseAgent.

#### Sections:
1. **BaseAgent Extension** — Custom agent structure
   - `_run_async_impl()` method override
   - Yielding events from custom logic
2. **InvocationContext** — Runtime access
   - Session, state, and agent tree access
   - User content and history
3. **Sub-Agent Orchestration** — Composing agents
   - Calling child agents from custom logic
   - State passing between agents

---

## Level 4: Multi-Agent Systems

### Workflow: Agent Delegation
> Scope: Route requests to specialized sub-agents.

#### Sections:
1. **Sub-Agent Configuration** — Defining child agents
   - `sub_agents` parameter on LlmAgent
   - Agent descriptions for routing
2. **Transfer of Control** — Delegation mechanics
   - Autonomous LLM-based routing
   - Manual transfer via `transfer_to_agent`
3. **Coordinator Patterns** — Central dispatcher design
   - Hub-and-spoke architecture
   - Context sharing between agents

---

### Workflow: Workflow Agents (Orchestration)
> Scope: Compose agents with deterministic execution patterns.

#### Sections:
1. **SequentialAgent** — Pipeline processing
   - Ordered sub-agent execution
   - State passing between stages
2. **ParallelAgent** — Concurrent execution
   - Fan-out/gather patterns
   - Result aggregation strategies
3. **LoopAgent** — Iterative refinement
   - `max_iterations` configuration
   - Exit conditions via `escalate`
4. **Nested Orchestration** — Complex workflows
   - Combining workflow agent types
   - Hierarchical agent structures

---

### Workflow: A2A Protocol (Agent-to-Agent)
> Scope: Enable interoperability between agents across different systems.

#### Sections:
1. **A2A Overview** — Protocol purpose and architecture
   - Agent discovery via Agent Cards
   - Task-based communication model
2. **Exposing Agents as A2A Services** — Server-side
   - `to_a2a()` utility function
   - AgentCard configuration
3. **Consuming A2A Services** — Client-side
   - `RemoteA2aAgent` integration
   - Cross-system agent composition

---

## Level 5: Memory & External Knowledge

### Workflow: Long-Term Memory
> Scope: Persist knowledge across sessions for user personalization.

#### Sections:
1. **MemoryService Configuration** — Storage setup
   - `InMemoryMemoryService` for testing
   - `VertexAiRagMemoryService` for production
2. **Memory Operations** — Store and retrieve
   - Automatic session-to-memory persistence
   - Query-based memory search
3. **Memory Integration** — Using in agents
   - Runner configuration with MemoryService
   - Context-aware memory injection

---

### Workflow: Grounding with External Data
> Scope: Connect agents to authoritative external knowledge sources.

#### Sections:
1. **Google Search Grounding** — Web-based facts
   - `google_search` tool configuration
   - Citation extraction from responses
2. **Vertex AI Search Grounding** — Enterprise data stores
   - Data store configuration
   - Hybrid search patterns
3. **Vertex AI RAG Engine** — Custom document retrieval
   - `VertexAiRagRetrieval` tool setup
   - Corpus creation and indexing

---

## Level 6: Safety & Security

### Workflow: Implementing Guardrails
> Scope: Protect agents from harmful inputs and outputs.

#### Sections:
1. **Input Guardrails** — Pre-LLM filtering
   - `before_model_callback` for content screening
   - Blocked topic detection
2. **Output Guardrails** — Post-LLM filtering
   - `after_model_callback` for response validation
   - Content safety filters
3. **Tool Guardrails** — Action validation
   - `before_tool_callback` for argument sanitization
   - In-tool security checks

---

### Workflow: Tool Authentication
> Scope: Securely connect tools to authenticated external services.

#### Sections:
1. **API Key Authentication** — Simple key-based access
   - `AuthCredentialTypes.API_KEY` configuration
   - Header vs query parameter placement
2. **OAuth2 Flows** — Token-based authentication
   - `OAuth2Auth` credential setup
   - Refresh token handling
3. **Credential Management** — Secure storage
   - `CredentialService` implementations
   - Session-state credential storage

---

### Workflow: Security Plugins
> Scope: Centralized policy enforcement via plugin architecture.

#### Sections:
1. **SecurityPlugin** — Tool call interception
   - Policy engine integration
   - Allow/deny decision patterns
2. **BasePolicyEngine** — Custom policy implementation
   - Action classification
   - Context-aware authorization

---

## Level 7: Streaming & Real-Time

### Workflow: SSE Streaming
> Scope: Stream agent responses via Server-Sent Events.

#### Sections:
1. **StreamingMode Configuration** — Enable SSE
   - `RunConfig` with `streaming_mode=SSE`
   - Progressive SSE (experimental)
2. **Response Handling** — Processing streams
   - Event iteration patterns
   - Partial response assembly

---

### Workflow: Bidirectional Streaming (BIDI)
> Scope: Full-duplex real-time communication via WebSocket.

#### Sections:
1. **Live API Integration** — WebSocket setup
   - `StreamingMode.BIDI` configuration
   - `LiveRequestQueue` for message passing
2. **Application Lifecycle** — Four-phase pattern
   - Initialization, session creation, interaction, cleanup
   - Agent-session mapping
3. **WebSocket Server Implementation** — FastAPI patterns
   - Upstream/downstream task architecture
   - Connection management

---

### Workflow: Audio, Video & Image Streaming
> Scope: Send and receive multimodal content in real-time streaming.

#### Sections:
1. **Supported Models** — Native audio/video models
   - `gemini-2.5-flash-native-audio-preview`
   - Platform compatibility (Gemini vs Vertex AI)
2. **Audio Input/Output** — Voice interactions
   - PCM audio format requirements
   - `send_realtime()` for audio chunks
   - Receiving audio in event stream
3. **Video and Image Input** — Visual content
   - Frame capture and encoding
   - Real-time video streaming
4. **Audio Transcription** — Speech-to-text
   - Automatic transcription in multi-agent
   - `AudioTranscriber` configuration

---

## Level 8: Deployment

### Workflow: Vertex AI Agent Engine Deployment
> Scope: Deploy agents to Google's managed Vertex AI runtime.

#### Sections:
1. **Prerequisites** — GCP setup
   - Staging bucket configuration
   - IAM permissions
   - Vertex AI API enablement
2. **CLI Deployment** — Using `adk deploy agent_engine`
   - Deployment command options
   - Tracing configuration (`--trace_to_cloud`)
3. **Agent Starter Pack** — Accelerated deployment
   - ASP tool installation
   - Makefile-based workflows
4. **Post-Deployment** — Querying deployed agents
   - Vertex AI SDK client usage
   - REST API access patterns
5. **Production Configuration** — Scaling and monitoring
   - Resource allocation
   - Cloud Trace integration

---

### Workflow: Cloud Run Deployment
> Scope: Deploy agents as containerized services on Cloud Run.

#### Sections:
1. **Project Structure** — Required files
   - `Dockerfile` configuration
   - `requirements.txt` dependencies
2. **CLI Deployment** — Using `adk deploy cloud_run`
   - Service name and region configuration
   - Environment variable injection
3. **Manual Deployment** — Using gcloud directly
   - `gcloud run deploy` command
   - Source-based vs image-based deployment
4. **Authentication** — Securing the service
   - Allow unauthenticated vs IAM-protected
   - Service account configuration

---

### Workflow: GKE Deployment
> Scope: Deploy agents to Google Kubernetes Engine.

#### Sections:
1. **Cluster Setup** — GKE prerequisites
   - Cluster creation and configuration
   - Autopilot vs Standard mode
2. **CLI Deployment** — Using `adk deploy gke`
   - Cluster name and service configuration
   - Artifact Registry integration
3. **Containerization** — Docker image building
   - Automatic image building
   - Registry push configuration
4. **Kubernetes Resources** — Deployment manifests
   - Deployment and Service creation
   - Ingress configuration

---

## Level 9: Observability & Evaluation

### Workflow: Tracing & Monitoring
> Scope: Instrument agents for production observability.

#### Sections:
1. **Cloud Trace Integration** — Distributed tracing
   - `--trace_to_cloud` flag
   - Trace visualization in GCP Console
2. **Logging Configuration** — Structured logs
   - ADK logging levels
   - Log export to Cloud Logging
   - `LoggingPlugin` for callback-based logging
3. **Custom Instrumentation** — Application-specific metrics
   - Callback-based timing
   - Performance profiling
4. **Third-Party Observability** — External platforms
   - AgentOps integration (2 lines of code)
   - Arize AX for production monitoring
   - Phoenix for self-hosted observability
   - Monocle open-source integration

---

### Workflow: Agent Evaluation
> Scope: Systematically test agent quality using golden datasets.

#### Sections:
1. **Test File Creation** — Single-turn test cases
   - JSON test file format
   - Input/output expectations
2. **Eval Set Definition** — Multi-turn conversations
   - Session-based evaluation
   - Trajectory validation
3. **Evaluation Criteria** — Quality metrics
   - Tool trajectory matching
   - LLM-based response assessment
4. **CI/CD Integration** — Automated testing
   - pytest integration
   - `adk web` evaluation UI
5. **User Simulation** — Synthetic user testing
   - Scenario file definition
   - `adk eval_set add_eval_case --scenarios_file`
   - Automated multi-turn conversation testing

---

## Level 10: Advanced Development

### Workflow: Visual Builder
> Scope: Build agents using a drag-and-drop UI (experimental).

#### Sections:
1. **Visual Builder Access** — Getting started
   - Vertex AI Console access
   - Workflow component support
2. **Agent Construction** — UI-based building
   - Drag-and-drop agent composition
   - AI-powered development assistant
3. **Export to Code** — From visual to Python
   - Exporting agent definitions
   - Customizing generated code

---

### Workflow: Thinking & Reasoning Configuration
> Scope: Enable and configure model reasoning capabilities.

#### Sections:
1. **ThinkingConfig** — Model thinking control
   - `include_thoughts` for reasoning visibility
   - `thinking_budget` token limits
2. **Built-in Planner** — Planning capabilities
   - `BuiltInPlanner` configuration
   - Plan-based execution patterns
3. **PlanReActPlanner** — Advanced reasoning
   - Plan-Re-Act methodology
   - NL planning request processing

---

## Summary

| Level | Focus Area | Key Workflows |
|-------|-----------|---------------|
| 1 | Foundation | Project init, basic agent, multi-model, **YAML config** |
| 2 | Tools | Function tools, **long-running**, built-in, OpenAPI, MCP, **3rd-party adapters**, **computer use** |
| 3 | Behavior | Callbacks, **confirmation flows**, plugins, state, artifacts, **events**, **custom agents** |
| 4 | Multi-Agent | Delegation, orchestration, A2A protocol |
| 5 | Memory | Long-term memory, grounding |
| 6 | Security | Guardrails, tool auth, security plugins |
| 7 | Streaming | SSE, BIDI, **audio/video multimodal** |
| 8 | Deployment | Agent Engine, **Cloud Run**, **GKE** |
| 9 | Quality | Tracing, **logging**, **3rd-party observability**, evaluation, **user simulation** |
| 10 | Advanced | **Visual Builder**, **thinking/reasoning** |

**Total Workflows: 35**

---

> **Next Step**: A downstream agent should create detailed workflow content for each section, referencing the source documentation paths identified during RAG retrieval.
