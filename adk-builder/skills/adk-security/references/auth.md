---
description: Implement authentication and authorization patterns for ADK tool integrations
---

# ADK Workflow: Tool Authentication

Implement OAuth2, API key, and other authentication patterns for tools that access external services.

---

## Prerequisites

- [ ] ADK project initialized
- [ ] External service credentials (OAuth client ID/secret or API key)
- [ ] Understanding of OAuth2 flow (for OAuth integrations)

```python
from google.adk.agents import LlmAgent
from google.adk.auth.auth_schemes import (
    AuthScheme,
    OpenIdConnectWithConfig,
    OAuth2WithConfig,
)
from google.adk.auth.auth_credential import (
    AuthCredential,
    AuthCredentialTypes,
    OAuth2Auth,
)
from google.adk.auth.auth_config import AuthConfig
from google.adk.tools.tool_context import ToolContext
```

---

## Step 1: Configure Authentication Scheme

Define the authentication scheme for your external service.

### OAuth2 / OpenID Connect

```python
import os

# OpenID Connect configuration (e.g., Google APIs)
auth_scheme = OpenIdConnectWithConfig(
    authorization_endpoint="https://accounts.google.com/o/oauth2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    scopes=["https://www.googleapis.com/auth/calendar.readonly"],
)

# Initial credential with client ID/secret
auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(
        client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
    ),
)
```

### API Key

```python
auth_scheme = AuthScheme(
    scheme_type="apiKey",
    api_key_config={
        "name": "X-API-Key",
        "in": "header",
    },
)

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.API_KEY,
    api_key="your-api-key-here",
)
```

---

## Step 2: Configure Tools with Authentication

### Using OpenAPI Tool Set

```python
from google.adk.tools.openapi_tool import OpenAPIToolset

# Create toolset from OpenAPI spec with auth
toolset = OpenAPIToolset.from_openapi_spec(
    spec_dict=openapi_spec,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential,
)

# Add to agent
agent = LlmAgent(
    name="api_agent",
    model="gemini-3-flash-preview",
    tools=toolset.tools,
)
```

### Using Google API Tool Sets

```python
from google.adk.tools.google_api_tool import calendar_tool_set

client_id = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
client_secret = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]

# Get calendar tools with OAuth configured
calendar_tools = calendar_tool_set(
    client_id=client_id,
    client_secret=client_secret,
)

agent = LlmAgent(
    name="calendar_agent",
    model="gemini-3-flash-preview",
    tools=calendar_tools,
)
```

---

## Step 3: Handle OAuth Flow in Custom Tools

For custom tools requiring OAuth, use `ToolContext.request_credential()`.

### Tool Implementation

```python
async def call_external_api(
    query: str,
    tool_context: ToolContext,
) -> dict:
    """Call external API requiring OAuth authentication."""
    
    # Define auth configuration
    auth_scheme = OpenIdConnectWithConfig(
        authorization_endpoint="https://provider.com/oauth/authorize",
        token_endpoint="https://provider.com/oauth/token",
        scopes=["read", "write"],
    )
    
    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=os.environ["PROVIDER_CLIENT_ID"],
            client_secret=os.environ["PROVIDER_CLIENT_SECRET"],
        ),
    )
    
    # Request credential - triggers OAuth flow if needed
    tool_context.request_credential(AuthConfig(
        auth_scheme=auth_scheme,
        raw_auth_credential=auth_credential,
    ))
    
    # Return pending status - ADK will handle OAuth flow
    return {"status": "pending", "message": "Authentication required"}
```

### Detecting Auth Completion

```python
async def call_external_api_with_token(
    query: str,
    tool_context: ToolContext,
) -> dict:
    """Call API after OAuth is complete."""
    
    # Check if we have a valid token
    auth_config = tool_context.get_auth_config()
    
    if not auth_config or not auth_config.exchanged_auth_credential:
        # No token yet - request credentials
        tool_context.request_credential(AuthConfig(
            auth_scheme=auth_scheme,
            raw_auth_credential=auth_credential,
        ))
        return {"status": "pending"}
    
    # We have a token - make the API call
    token = auth_config.exchanged_auth_credential.oauth2.access_token
    
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.provider.com/data",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query},
        )
        return response.json()
```

---

## Step 4: Handle OAuth Callback in Runner Loop

The Runner handles OAuth flow events automatically. For CLI applications:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

async def run_with_auth():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="my_app", user_id="user1")
    
    runner = Runner(agent=agent, session_service=session_service)
    
    async for event in runner.run_async(
        session_id=session.id,
        user_id="user1",
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text("Check my calendar")]
        ),
    ):
        # Check for auth request
        if hasattr(event, "actions") and event.actions:
            for action in event.actions.actions:
                if action.auth_config:
                    # OAuth flow needed
                    auth_url = action.auth_config.exchanged_auth_credential.oauth2.auth_uri
                    print(f"Please authenticate: {auth_url}")
                    
                    # Get callback URL from user
                    callback_url = input("Paste callback URL: ")
                    
                    # Submit auth response
                    await runner.handle_auth_response(
                        session_id=session.id,
                        auth_response_uri=callback_url,
                    )
        
        # Handle normal events
        if hasattr(event, "content") and event.content:
            print(event.content.parts[0].text)
```

---

## Authentication Types Reference

| Type | Use Case | Credential Class |
|------|----------|------------------|
| `API_KEY` | Simple API key auth | `AuthCredential(auth_type=AuthCredentialTypes.API_KEY, api_key="...")` |
| `HTTP_BASIC` | Basic auth | `AuthCredential(auth_type=AuthCredentialTypes.HTTP, http=HttpAuth(...))` |
| `OAUTH2` | OAuth2/OIDC flows | `AuthCredential(auth_type=AuthCredentialTypes.OAUTH2, oauth2=OAuth2Auth(...))` |
| `SERVICE_ACCOUNT` | GCP service accounts | `AuthCredential(auth_type=AuthCredentialTypes.SERVICE_ACCOUNT, ...)` |

---

## Identity Considerations

Different identity models for tool authorization:

| Model | Description | Use Case |
|-------|-------------|----------|
| **Agent Identity** | Tools use agent's service account | Backend operations, no user context |
| **User Identity** | Tools use user's OAuth token | User-specific data access (calendar, email) |
| **Hybrid** | Different tools use different identities | Mixed workloads |

```python
# User identity: OAuth flow
calendar_tools = calendar_tool_set(
    client_id=client_id,
    client_secret=client_secret,
)

# Agent identity: Service account
from google.oauth2 import service_account

agent_creds = service_account.Credentials.from_service_account_file(
    "service_account.json"
)
```

---

## Verification

```bash
adk run your_agent_folder
```

Test the OAuth flow:
1. Request an action requiring auth (e.g., "Check my calendar")
2. Expect auth URL to be provided
3. Complete OAuth in browser
4. Paste callback URL
5. Verify the action completes with authenticated data

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Auth pending" loops forever | Callback URL not processed | Ensure `handle_auth_response()` is called |
| Invalid redirect URI | OAuth config mismatch | Verify redirect URI in OAuth provider matches |
| Token expired | No refresh token handling | Include `offline_access` scope; ADK refreshes automatically |
| Missing `tool_context` | Not in function signature | Add `tool_context: ToolContext` parameter |

---

## References

- ADK Tool Authentication Guide
- ADK Context: Handling Tool Authentication
- ADK Examples: OAuth CLI Flow
