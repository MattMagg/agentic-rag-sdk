---
description: Configure logging levels and debug output for ADK agent development
---

# ADK Workflow: Quality Logging

Configure logging in ADK to debug agent behavior, inspect LLM prompts, and troubleshoot tool execution. ADK uses Python's standard `logging` module with the `google_adk` logger.

---

## Prerequisites

- [ ] ADK Python v0.1.0+
- [ ] Python logging module (builtin)

```python
import logging
```

---

## Step 1: Configure Log Level

### Basic Setup

```python
import logging

# Set log level for the ADK logger
logging.getLogger('google_adk').setLevel(logging.DEBUG)
```

### Using ADK Helper

```python
from google.adk.cli.utils.logs import setup_adk_logger

# Configure with desired level
setup_adk_logger(level=logging.DEBUG)
```

---

## Step 2: Log Levels Reference

ADK uses standard Python log levels:

| Level | Value | Description | Type of Information Logged |
|-------|-------|-------------|---------------------------|
| `DEBUG` | 10 | Detailed diagnostic information | LLM prompts, tool arguments, internal state |
| `INFO` | 20 | General operational information | Agent start/stop, major events |
| `WARNING` | 30 | Potential issues | Deprecated features, recoverable errors |
| `ERROR` | 40 | Errors that need attention | Failed tool calls, LLM errors |
| `CRITICAL` | 50 | Serious failures | System-level failures |

---

## Step 3: Debug Output with runner.run_debug()

Use `run_debug()` for quick interactive debugging:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from your_agent import root_agent

runner = Runner(
    agent=root_agent,
    session_service=InMemorySessionService(),
    app_name="debug-agent",
)

# Run with debug output
await runner.run_debug(
    "What is the weather in San Francisco?",
    verbose=True,  # Shows tool calls and details
)
```

### Verbose Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `verbose` | bool | False | Show tool calls and detailed output |
| `user_id` | str | "debug_user_id" | User ID for the session |
| `session_id` | str | "debug_session_id" | Session ID |

---

## Step 4: Using LoggingPlugin

The `LoggingPlugin` logs events at each callback point:

```python
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.agents import Agent

# Create agent with logging plugin
agent = Agent(
    name="logged_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful assistant.",
    plugins=[LoggingPlugin()],
)
```

---

## Step 5: Log to File

For persistent logging to a file:

```python
from google.adk.cli.utils.logs import log_to_tmp_folder

# Log to /tmp/agents_log/agent_YYYYMMDD_HHMMSS.log
log_to_tmp_folder(
    level=logging.DEBUG,
    sub_folder='agents_log',
    log_file_prefix='agent',
)
```

---

## Step 6: Debugging Common Issues

### Scenario: Inspect LLM Prompt

When the agent produces unexpected output, enable DEBUG logging:

```python
import logging

# Enable debug for complete request/response visibility
logging.getLogger('google_adk').setLevel(logging.DEBUG)

# Run your agent - logs will show:
# - Full prompt sent to LLM
# - Model response
# - Tool call arguments
```

### Scenario: A2A Debugging

Add logging for A2A (Agent-to-Agent) communication:

```python
import logging

# Enable A2A debug logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

# Start remote A2A server with logging
# adk api_server --a2a --port 8001 your_agent
```

---

## Step 7: Custom Event Printing

For custom formatted output, use the debug utilities:

```python
from google.adk.utils._debug_output import print_event

async for event in runner.run_async(...):
    # Print event in user-friendly format
    print_event(event, verbose=True)
```

---

## Configuration Reference

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ADK_LOG_LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |

### CLI Flags

| Flag | Description |
|------|-------------|
| `adk run --verbose` | Enable verbose output |
| `adk web --log-level DEBUG` | Set log level for dev server |

---

## Verification

Test your logging configuration:

```python
import logging

# Configure
logging.getLogger('google_adk').setLevel(logging.DEBUG)

# Run agent and verify output shows:
# 1. LLM request/response details
# 2. Tool call arguments and results
# 3. State transitions
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No logs visible | Logger not configured | Call `setup_adk_logger()` or set level directly |
| Too much output | Level too verbose | Use INFO instead of DEBUG for production |
| Logs not in file | File handler missing | Use `log_to_tmp_folder()` for file output |
| Missing tool logs | Verbose flag off | Set `verbose=True` in `run_debug()` |

---

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
