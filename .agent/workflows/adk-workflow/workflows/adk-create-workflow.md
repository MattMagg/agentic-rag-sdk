---
description: Template for creating ADK workflows via RAG-grounded research
---

# ADK Workflow Creation Template

You are creating a new ADK workflow. This template guides you through RAG-based research to build a comprehensive, grounded workflow.

**Input Required:** Workflow name (e.g., `adk-tools-function`, `adk-streaming-bidi`)

---

## Step 1: Parse the Workflow Target

Extract the workflow topic from the name:

```
adk-tools-function      → FunctionTool, ToolContext
adk-behavior-callbacks  → before_agent_callback, after_model_callback
adk-memory-grounding    → google_search, VertexAiRagRetrieval
adk-streaming-bidi      → StreamingMode.BIDI, WebSocket, run_live
adk-deploy-cloudrun     → Cloud Run, adk deploy cloud_run
```

**Write down:** The core ADK concepts this workflow must cover.

---

## Step 2: Execute RAG Discovery Queries

Run 3-5 targeted queries using the RAG system:

```bash
# Query 1: Core concept documentation
python -m src.grounding.query.query_adk "[TOPIC] documentation guide" --verbose --top-k 12

# Query 2: Implementation patterns
python -m src.grounding.query.query_adk "[TOPIC] class implementation example" --verbose --top-k 12

# Query 3: Configuration options
python -m src.grounding.query.query_adk "[TOPIC] configuration parameters options" --verbose --top-k 10

# Query 4: Common patterns and best practices
python -m src.grounding.query.query_adk "[TOPIC] best practices patterns" --verbose --top-k 10

# Query 5: Integration with other components
python -m src.grounding.query.query_adk "[TOPIC] integration callback state" --verbose --top-k 10
```

**Record:** Key documentation paths, class names, method signatures, and code examples from results.

---

## Step 3: Identify Required Sections

Based on RAG results, determine workflow sections:

| Section Type | Include If... |
|--------------|---------------|
| Prerequisites | Setup, imports, or dependencies required |
| Core Implementation | Primary API/class usage |
| Configuration Options | Multiple configuration parameters exist |
| Integration Points | Connects to callbacks, state, or other systems |
| Verification Steps | How to test the implementation |
| Common Patterns | Multiple usage patterns discovered |
| Troubleshooting | Known issues or error patterns found |

---

## Step 4: Extract Code Examples

From RAG results, extract:

1. **Import statements** - What to import
2. **Class instantiation** - How to create the object
3. **Method calls** - Key methods and their signatures
4. **Configuration objects** - Parameter classes and options
5. **Integration code** - How it connects to LlmAgent or Runner

**Format as executable code blocks** with proper syntax highlighting.

---

## Step 5: Write the Workflow File

Create the workflow at `.agent/workflows/adk-{parent}-{child}.md` using this structure:

```markdown
---
description: [One-line description of what this workflow accomplishes]
---

# ADK Workflow: [Title]

[Brief scope statement]

---

## Prerequisites

- [ ] [Required setup item]
- [ ] [Required import or dependency]

---

## Step 1: [First Major Step]

[Explanation grounded in RAG findings]

```python
# Code example from documentation
```

---

## Step 2: [Second Major Step]

[Continue with implementation steps]

---

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| [param] | [type] | [default] | [from docs] |

---

## Integration Points

- **With Callbacks:** [How it integrates]
- **With State:** [How it integrates]
- **With Runner:** [How it integrates]

---

## Verification

```bash
# Command to verify
adk run agent_folder
```

Expected behavior: [What should happen]

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| [Error] | [Why] | [Fix] |

---

## References

- [doc_path_1](file path from RAG)
- [doc_path_2](file path from RAG)
```

---

## Step 6: Validate the Workflow

Check that your workflow:

- [ ] All code examples are syntactically correct
- [ ] All imports exist in the ADK package
- [ ] All method signatures match the source code
- [ ] All parameter names/types are accurate
- [ ] References cite actual documentation paths
- [ ] Verification steps are executable

---

## Step 7: Register in Master Workflow

Update `/adk-master` to include routing to the new workflow:

1. Add to keyword routing map
2. Add to reference section
3. Update any relevant chaining examples

---

## Example: Creating `adk-behavior-callbacks`

### RAG Queries Executed:
```bash
python -m src.grounding.query.query_adk "callbacks before_tool_callback after_model_callback" --verbose
python -m src.grounding.query.query_adk "callback context CallbackContext" --verbose
python -m src.grounding.query.query_adk "callback return value skip agent" --verbose
```

### Key Findings:
- `docs/callbacks/index.md` - Overview and mechanism
- `docs/callbacks/types-of-callbacks.md` - All callback types
- `docs/callbacks/design-patterns-and-best-practices.md` - Patterns
- `src/google/adk/agents/llm_agent.py` - Callback signatures

### Resulting Sections:
1. Prerequisites (imports)
2. Callback Types (agent, model, tool)
3. CallbackContext Usage
4. Return Value Patterns (skip, modify, pass-through)
5. Design Patterns
6. Verification
7. References

---

## Quick Reference: RAG Query Patterns

```bash
# For tool workflows
"[ToolName] class usage example"
"[ToolName] configuration parameters"

# For behavior workflows
"[Feature] callback integration"
"[Feature] state management"

# For deployment workflows
"deploy [target] configuration"
"[target] deployment prerequisites"

# For streaming workflows
"StreamingMode [mode] setup"
"[mode] WebSocket implementation"
```
