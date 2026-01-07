---
description: Integrate REST APIs as agent tools using OpenAPI specifications
---

# ADK Workflow: OpenAPI Tools Integration

Integrate external REST APIs into your ADK agent using OpenAPI (Swagger) specification documents. The `OpenAPIToolset` class automatically parses your OpenAPI spec and generates callable tools for each API operation.

---

## Prerequisites

- [ ] ADK Python v0.1.0+ installed
- [ ] OpenAPI specification document (JSON or YAML format)
- [ ] API credentials if authentication is required

---

## Step 1: Obtain Your OpenAPI Specification

Get your OpenAPI specification document from one of these sources:

- **Local file**: Load from `.json` or `.yaml` file
- **Remote URL**: Fetch from API documentation endpoint
- **String content**: Parse inline specification

```python
import json

# Option A: Load from file
with open("openapi.json", "r") as f:
    spec_dict = json.load(f)

# Option B: Load from YAML file
import yaml
with open("openapi.yaml", "r") as f:
    spec_dict = yaml.safe_load(f)
```

---

## Step 2: Create the OpenAPIToolset

Initialize the toolset by providing your OpenAPI specification:

```python
from google.adk.tools.openapi_tool import OpenAPIToolset

# Initialize from dictionary
openapi_toolset = OpenAPIToolset(spec_dict=spec_dict)

# Alternative: Initialize from string
openapi_toolset = OpenAPIToolset(spec_str=spec_string)

# Alternative: Initialize from URL
openapi_toolset = OpenAPIToolset(spec_url="https://api.example.com/openapi.json")
```

Each API operation defined in your OpenAPI spec becomes a `RestApiTool` that your agent can invoke.

---

## Step 3: Configure Authentication (If Required)

For APIs requiring authentication, provide the auth scheme and credentials:

```python
from google.adk.auth.auth_schemes import APIKey, OAuth2, OpenIdConnectWithConfig
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes

# Example: API Key authentication
auth_scheme = APIKey(
    in_="header",       # Location: "header", "query", or "cookie"
    name="X-API-Key"    # Name of the header/query parameter
)

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.API_KEY,
    api_key="your-api-key-here"
)

# Initialize toolset with authentication
openapi_toolset = OpenAPIToolset(
    spec_dict=spec_dict,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)
```

### OAuth2 Authentication

```python
from google.adk.auth.auth_schemes import OAuth2
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth

auth_scheme = OAuth2(
    flows={
        "authorizationCode": {
            "authorizationUrl": "https://auth.example.com/authorize",
            "tokenUrl": "https://auth.example.com/token",
            "scopes": {"read": "Read access", "write": "Write access"}
        }
    }
)

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
)
```

---

## Step 4: Add Toolset to Your Agent

Include the toolset in your agent's tools list:

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="api_agent",
    instruction="""You are an assistant that helps users interact with 
    external APIs. Use the available tools to fulfill user requests.""",
    tools=[openapi_toolset]
)
```

---

## Step 5: Access Individual Tools (Optional)

You can access specific tools from the toolset:

```python
# Get all tools from the toolset
all_tools = openapi_toolset.get_tools()

# Get a specific tool by operation name
specific_tool = openapi_toolset.tool("get_users_list")

# Configure auth on individual tool
specific_tool.configure_auth_scheme(auth_scheme)
specific_tool.configure_auth_credential(auth_credential)
```

---

## Configuration Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `spec_dict` | `Dict` | OpenAPI spec as Python dictionary |
| `spec_str` | `str` | OpenAPI spec as JSON/YAML string |
| `spec_url` | `str` | URL to fetch OpenAPI spec from |
| `auth_scheme` | `AuthScheme` | Authentication scheme (APIKey, OAuth2, etc.) |
| `auth_credential` | `AuthCredential` | Credentials for authentication |

---

## RestApiTool Parameters

Each `RestApiTool` generated from the spec has these properties:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Tool name (derived from `operationId`) |
| `description` | `str` | Tool description (from operation summary) |
| `endpoint` | `OperationEndpoint` | API endpoint (path + method) |
| `operation` | `Operation` | OpenAPI operation object |

---

## Integration Points

- **With Callbacks:** Use `before_tool_callback` to intercept and modify API requests before execution
- **With State:** API responses can be stored in session state for later use
- **With Authentication Flow:** Supports OAuth2 refresh token flows via `tool_context.request_credential()`

---

## Verification

```bash
# Create and run the agent
adk run api_agent_folder
```

**Expected behavior:** 
1. Agent loads the OpenAPI specification
2. Each API operation becomes an available tool
3. When the user asks to perform an API action, the agent calls the appropriate tool
4. API responses are returned to the user

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Tool not found" | Operation ID doesn't match | Check `operationId` in OpenAPI spec matches tool name |
| 401 Unauthorized | Missing/invalid credentials | Verify `auth_scheme` and `auth_credential` are correctly configured |
| Schema validation error | Malformed OpenAPI spec | Validate spec at [Swagger Editor](https://editor.swagger.io/) |
| Parameter type mismatch | Wrong parameter format | Check `in` property: path, query, header, or cookie |

---

## Complete Example

```python
import json
from google.adk.agents import LlmAgent
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.adk.auth.auth_schemes import APIKey
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes

# Load OpenAPI spec
with open("petstore.json", "r") as f:
    spec = json.load(f)

# Configure authentication
auth_scheme = APIKey(in_="header", name="api_key")
auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.API_KEY,
    api_key="demo-api-key"
)

# Create toolset
toolset = OpenAPIToolset(
    spec_dict=spec,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)

# Create agent
agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="petstore_agent",
    instruction="Help users manage their pet store inventory.",
    tools=[toolset]
)
```

---

## References

- OpenAPI Tools Documentation: `docs/tools-custom/openapi-tools.md`
- Authentication Guide: `docs/tools-custom/authentication.md`
- OpenAPIToolset Implementation: `src/google/adk/tools/openapi_tool/openapi_spec_parser/openapi_toolset.py`
- RestApiTool Implementation: `src/google/adk/tools/openapi_tool/openapi_spec_parser/rest_api_tool.py`
