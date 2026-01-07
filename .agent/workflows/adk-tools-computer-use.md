---
description: Enable browser and desktop automation using Computer Use Toolset
---

# ADK Workflow: Computer Use Tools

Enable your ADK agent to interact with computer environments (browser or desktop) using the Computer Use Toolset. This allows agents to take screenshots, click elements, type text, scroll, and press keys.

> [!WARNING]
> Computer Use is a **Preview** feature available in ADK Python v1.17.0+. APIs may change.

---

## Prerequisites

- [ ] ADK Python v1.17.0+ installed
- [ ] Gemini model with computer use support (e.g., `gemini-3-flash-preview`)
- [ ] Custom `BaseComputer` implementation for your target environment

---

## Overview: Architecture

The Computer Use system consists of:

| Component | Description |
|-----------|-------------|
| `ComputerUseToolset` | Main toolset providing computer control tools |
| `BaseComputer` | Abstract interface for computer environments |
| `ComputerUseTool` | Individual tools (click, type, screenshot, etc.) |
| `ComputerEnvironment` | Environment type: BROWSER or DESKTOP |

---

## Step 1: Understand the BaseComputer Interface

`BaseComputer` is an abstract base class defining the interface for computer environments:

```python
from google.adk.tools.computer_use.base_computer import BaseComputer, ComputerState

class BaseComputer(abc.ABC):
    """Abstract interface for computer environments."""
    
    @abstractmethod
    async def screen_size(self) -> tuple[int, int]:
        """Return (width, height) of the screen."""
        pass
    
    @abstractmethod
    async def screenshot(self) -> bytes:
        """Capture and return screenshot as PNG bytes."""
        pass
    
    @abstractmethod
    async def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at coordinates (x, y)."""
        pass
    
    @abstractmethod
    async def type_text(self, text: str) -> None:
        """Type the given text."""
        pass
    
    @abstractmethod
    async def key(self, key: str) -> None:
        """Press a keyboard key."""
        pass
    
    @abstractmethod
    async def scroll(self, x: int, y: int, delta_x: int, delta_y: int) -> None:
        """Scroll at position (x, y) by (delta_x, delta_y)."""
        pass
```

---

## Step 2: Implement a Custom BaseComputer

Create a concrete implementation for your target environment:

### Example: Browser Automation with Playwright

```python
from google.adk.tools.computer_use.base_computer import BaseComputer, ComputerEnvironment

class PlaywrightComputer(BaseComputer):
    """Browser automation using Playwright."""
    
    def __init__(self):
        self._page = None
        self._browser = None
        self._playwright = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self._page = await self._browser.new_page()
    
    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    @property
    def environment(self) -> ComputerEnvironment:
        return ComputerEnvironment.ENVIRONMENT_BROWSER
    
    async def screen_size(self) -> tuple[int, int]:
        viewport = self._page.viewport_size
        return (viewport["width"], viewport["height"])
    
    async def screenshot(self) -> bytes:
        return await self._page.screenshot(type="png")
    
    async def click(self, x: int, y: int, button: str = "left") -> None:
        await self._page.mouse.click(x, y, button=button)
    
    async def type_text(self, text: str) -> None:
        await self._page.keyboard.type(text)
    
    async def key(self, key: str) -> None:
        await self._page.keyboard.press(key)
    
    async def scroll(self, x: int, y: int, delta_x: int, delta_y: int) -> None:
        await self._page.mouse.move(x, y)
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def navigate(self, url: str) -> None:
        """Navigate to a URL (browser-specific)."""
        await self._page.goto(url)
```

---

## Step 3: Create ComputerUseToolset

```python
from google.adk.tools.computer_use import ComputerUseToolset

# Create your computer implementation
my_computer = PlaywrightComputer()

# Create the toolset
computer_toolset = ComputerUseToolset(computer=my_computer)
```

---

## Step 4: Add to Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="browser_agent",
    instruction="""You are an AI assistant that can control a web browser.
    You can:
    - Take screenshots to see the current state
    - Click on elements at specific coordinates
    - Type text into input fields
    - Press keyboard keys
    - Scroll the page
    
    Always take a screenshot first to understand the current page state
    before taking any actions.""",
    tools=[computer_toolset]
)
```

---

## Step 5: Run the Agent

```python
import asyncio
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Initialize the computer
    my_computer = PlaywrightComputer()
    await my_computer.initialize()
    
    try:
        # Create toolset and agent
        toolset = ComputerUseToolset(computer=my_computer)
        
        agent = LlmAgent(
            model="gemini-3-flash-preview",
            name="browser_agent",
            instruction="Control the browser to help users.",
            tools=[toolset]
        )
        
        # Create runner
        runner = Runner(
            agent=agent,
            app_name="browser_automation"
        )
        
        # Navigate to starting page
        await my_computer.navigate("https://example.com")
        
        # Run interaction
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.Content(
                role="user",
                parts=[types.Part.from_text("Click the login button")]
            )
        ):
            print(event)
    
    finally:
        await my_computer.close()

asyncio.run(main())
```

---

## Available Tools

The `ComputerUseToolset` provides these tools to the agent:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `screenshot` | Capture current screen state | None |
| `click` | Click at coordinates | `x`, `y`, `button` |
| `type` | Type text | `text` |
| `key` | Press keyboard key | `key` |
| `scroll` | Scroll at position | `x`, `y`, `delta_x`, `delta_y` |

---

## Configuration Options

### ComputerUseToolset Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `computer` | `BaseComputer` | Required. The computer implementation to control |

### ComputerEnvironment Values

| Value | Description |
|-------|-------------|
| `ENVIRONMENT_UNSPECIFIED` | Defaults to browser |
| `ENVIRONMENT_BROWSER` | Web browser environment |
| `ENVIRONMENT_DESKTOP` | Desktop operating system |

---

## ComputerState Model

The computer state returned by some operations:

```python
from google.adk.tools.computer_use.base_computer import ComputerState

class ComputerState(pydantic.BaseModel):
    screenshot: bytes      # Screenshot as PNG bytes
    url: Optional[str]     # Current URL (browser only)
    title: Optional[str]   # Page/window title
```

---

## Integration Points

- **With Screenshot Analysis:** Gemini analyzes screenshots to determine next actions
- **With Agent Instructions:** Guide the agent on when and how to use computer controls
- **With Callbacks:** Use tool callbacks to log or modify computer actions

---

## Verification

```bash
# Run the agent
python -m my_agent.main
```

**Expected behavior:**
1. Browser opens and navigates to the target page
2. Agent takes a screenshot to analyze the page
3. Agent performs actions based on user request
4. Agent confirms action completion with another screenshot

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "No module named 'playwright'" | Playwright not installed | Run `pip install playwright && playwright install` |
| Screenshot returns empty | Browser not initialized | Ensure `await computer.initialize()` is called |
| Clicks miss target | Coordinate mismatch | Verify virtual coordinate space matches actual viewport |
| System instruction error | Known Gemini limitation | Computer use may require disabling system instructions |

---

## Important Notes

> [!IMPORTANT]
> Computer Use with Gemini may have specific restrictions:
> - System instructions may be disabled when computer use is active
> - The model needs to "see" screenshots to understand page state
> - Always take a screenshot before and after actions for verification

---

## References

- Computer Use Documentation: `docs/tools/gemini-api/computer-use.md`
- BaseComputer Implementation: `src/google/adk/tools/computer_use/base_computer.py`
- ComputerUseToolset Implementation: `src/google/adk/tools/computer_use/computer_use_toolset.py`
- ComputerUseTool Implementation: `src/google/adk/tools/computer_use/computer_use_tool.py`
