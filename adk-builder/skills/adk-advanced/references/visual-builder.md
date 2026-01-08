---
description: Build agents visually using ADK's drag-and-drop interface with AI-powered development assistance
---

# ADK Workflow: Visual Builder for Agents

Use ADK's Visual Builder to design, build, and test agents in a web-based graphical interface with an AI-powered development assistant.

> [!NOTE]
> **Version:** Requires ADK Python v1.18.0+
> **Status:** Experimental feature

---

## Prerequisites

- [ ] ADK Python installed (`pip install google-adk`)
- [ ] Write access to a development directory (agent files will be created here)
- [ ] Model API access configured (Google AI or Vertex AI)

---

## Step 1: Launch Visual Builder

Start the ADK Web interface from your development directory:

```bash
# Navigate to your development directory
cd ~/my-adk-projects

# Launch ADK Web with Visual Builder
adk web --port 8000
```

> [!TIP]
> Visual Builder writes project files to subdirectories where you run `adk web`. Make sure you run from a development directory with write access.

Open your browser to `http://localhost:8000`

---

## Step 2: Create a New Agent

1. In the top left of the page, select the **+** (plus sign)
2. Type a name for your agent application
3. Select **Create**

---

## Step 3: Design Your Agent

Use the three-panel interface:

| Panel | Purpose |
|-------|---------|
| **Left Panel** | Edit agent component values (name, model, instructions) |
| **Central Panel** | Add new agent components (drag-and-drop) |
| **Right Panel** | AI-powered assistant for help and modifications |

---

## Step 4: Add Components

### Supported Agent Types

| Component | Description |
|-----------|-------------|
| **Root Agent** | Primary controlling agent for the workflow |
| **LLM Agent** | Agent powered by a generative AI model |
| **Sequential Agent** | Executes sub-agents in sequence |
| **Loop Agent** | Repeatedly executes a sub-agent until condition is met |
| **Parallel Agent** | Executes multiple sub-agents concurrently |

### Supported Tools

| Tool Type | How to Add |
|-----------|------------|
| **Prebuilt Tools** | Select from available ADK tools |
| **Custom Tools** | Specify fully-qualified Python function name |

### Supported Components

| Component | Purpose |
|-----------|---------|
| **Callbacks** | Modify agent behavior at workflow events |

---

## Step 5: Use the AI Assistant

The right panel provides an AI-powered development assistant. Example prompts:

```
Help me add a dice roll tool to my current agent.
Use the default model if you need to configure that.
```

```
Add a sub-agent that handles customer support queries.
```

```
Configure my agent to use the google_search tool.
```

---

## Step 6: Save Your Agent

1. In the bottom left corner, select **Save**
2. Your agent files are generated in the development directory

> [!CAUTION]
> Always save before exiting the editing interface. Unsaved agents may not be editable later.

---

## Step 7: Test Your Agent

1. Interact with your agent in the ADK Web interface
2. View conversation history and agent responses
3. Debug and iterate on your design

---

## Step 8: Continue Editing

To edit an existing Visual Builder agent:

1. In the top left, select the **pencil icon** (edit)
2. Make changes using the three-panel interface
3. Save your changes

> [!IMPORTANT]
> The edit (pencil) icon is **only available** for agents created with Visual Builder

---

## Project Code Output

Visual Builder generates code in the Agent Config format:

```
YourAgent/
    root_agent.yaml    # Main agent configuration
    sub_agent_1.yaml   # Sub-agent configs (if any)
    tools/             # Tools directory
        __init__.py
        custom_tool.py # Tool implementations
```

---

## Configuration Options

### Agent YAML Structure

```yaml
name: my_agent
model: gemini-3-flash-preview
description: "A helpful assistant"
instruction: |
  You are a helpful assistant that...
tools:
  - google_search
sub_agents:
  - $ref: sub_agent_1.yaml
```

---

## Integration Points

- **With Agent Config:** Visual Builder outputs are in YAML Agent Config format
- **With adk run:** Deploy generated agents via CLI
- **With adk web:** Test agents interactively
- **With Code Editing:** Generated files can be manually edited (with caveats)

---

## Verification

```bash
# Run your Visual Builder agent
adk run YourAgent

# Or test via web interface
adk web --port 8000
```

**Expected behavior:**
- Agent responds according to configured instructions
- Tools execute when called by the LLM
- Sub-agents are invoked appropriately

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Cannot edit agent | Agent not created with Visual Builder | Edit YAML files directly instead |
| Agent not saved | Exited editing mode without saving | Recreate the agent |
| Custom tool not found | Incorrect Python path | Use fully-qualified name (e.g., `my_pkg.tools.my_function`) |
| Unsupported feature | Agent Config limitations | See Agent Config known limitations |

---

## Known Limitations

Some advanced ADK features are not supported due to Agent Config limitations:

- Complex callback structures
- Dynamic agent composition at runtime
- Some advanced tool configurations

For advanced use cases, consider building agents in Python directly.

---

## Example: Building a Dice Agent

Using the AI Assistant:

```
1. Create a new agent called "DiceAgent"
2. In the right panel, type: "Help me add a dice roll tool to my current agent"
3. Follow the assistant's guidance
4. Save and test
```

Generated output:

```
DiceAgent/
    root_agent.yaml
    tools/
        __init__.py
        dice_tool.py
```

---

## Next Steps

- **Edit generated files:** Customize the YAML and Python code in your IDE
- **Deploy your agent:** Use `adk deploy` for production deployment
- **Add more tools:** Extend functionality with custom tools
- **Learn Agent Config:** See Agent Config documentation for YAML options

---

## References

- [ADK Visual Builder Documentation](https://google.github.io/adk-docs/visual-builder/)
- [ADK Agent Config](https://google.github.io/adk-docs/agents/config/)
- [Agent Config YAML Schema](https://google.github.io/adk-docs/api-reference/agentconfig/)
- [ADK Installation Guide](https://google.github.io/adk-docs/get-started/installation/)
