Here is a comprehensive CLI cheat sheet for the Google Agent Development Kit (ADK) and Vertex AI Agent Engine, categorized by workflow phase.

### **1. Installation & Setup**
Commands to install the framework and manage the environment.

| Command | Description | Source |
| :--- | :--- | :--- |
| `pip install google-adk` | Installs the core ADK Python library. |, |
| `pip install "google-adk[vertexai]"` | Installs ADK with additional dependencies required for Vertex AI features (like Sessions/Memory). |, |
| `adk --version` | Verifies the installed version of the ADK CLI. | |
| `gcloud auth application-default login` | Authenticates your local environment with Google Cloud (required for Vertex AI backends). |, |
| `gcloud config set project <PROJECT_ID>` | Sets the active Google Cloud project for the CLI session. |, |

---

### **2. Scaffolding & Creation**
Commands to generate the directory structure and boilerplate code for new agents.

| Command | Description | Source |
| :--- | :--- | :--- |
| `adk create <agent_name>` | Generates a new agent project structure (includes `agent.py`, `__init__.py`, `.env`). |, |
| `uvx agent-starter-pack create <name> -a <template>` | Bootstraps a production-ready agent project with CI/CD and Terraform infrastructure. | |

---

### **3. Local Development & Testing**
Commands to run the agent locally for debugging and interaction.

| Command | Description | Source |
| :--- | :--- | :--- |
| `adk run <agent_name>` | Launches the agent in an interactive CLI chat session. |, |
| `adk web` | Launches the browser-based **Developer UI** for visual debugging, tracing, and chat. |, |
| `adk web --port <port_number>` | Launches the Developer UI on a specific port (default is 8000). | |
| `adk api_server` | Starts a local FastAPI server exposing the agent via REST endpoints (useful for cURL testing). |, |
| `echo "prompt" | adk run <agent_name>` | Pipes a text prompt directly into the agent for single-turn testing. | |

---

### **4. Evaluation**
Commands to assess agent quality and performance against datasets.

| Command | Description | Source |
| :--- | :--- | :--- |
| `adk eval <agent_path> <evalset_path>` | Runs an automated evaluation of the agent using a specific `.evalset.json` file. | |
| `adk eval ... --print_detailed_results` | Runs evaluation and prints granular details of pass/fail criteria to the console. | |
| `pytest tests/integration/` | Runs programmatic integration tests (if configured using `AgentEvaluator`). | |

---

### **5. Deployment**
Commands to deploy the agent to Google Cloud runtime environments.

| Command | Description | Source |
| :--- | :--- | :--- |
| `adk deploy agent_engine` | Deploys the agent to the managed **Vertex AI Agent Engine**. |, |
| `adk deploy cloud_run` | Deploys the agent as a containerized service to **Cloud Run**. | |
| `adk deploy gke` | Deploys the agent to a **Google Kubernetes Engine** cluster. | |

**Common Deployment Flags:**
*   `--project <PROJECT_ID>`: Specifies the target Google Cloud project.
*   `--region <REGION>`: Specifies the region (e.g., `us-central1`).
*   `--staging_bucket gs://<BUCKET>`: Specifies the GCS bucket for staging artifacts during deployment.
*   `--requirements_file <PATH>`: Points to the `requirements.txt` file for dependencies.

---

### **6. Governance & Utility**
Commands for managing tools and resources via the Cloud API Registry.

| Command | Description | Source |
| :--- | :--- | :--- |
| `gcloud beta api-registry mcp servers list` | Lists available Model Context Protocol (MCP) servers in the project. | |
| `gcloud beta api-registry mcp enable <service>` | Enables a specific Google Cloud service (e.g., `bigquery.googleapis.com`) as an MCP server. | |

---

### **7. Process Management (macOS/Linux)**
Commands for handling port conflicts and managing background processes.

| Command | Description |
| :--- | :--- |
| `lsof -i:<PORT>` | Lists processes using a specific port (e.g., `lsof -i:8000`). |
| `lsof -ti:<PORT>` | Returns only the PID of the process using the port (silent mode). |
| `lsof -ti:<PORT> \| xargs kill -9` | Finds and force-kills the process using the specified port. |
| `ps aux \| grep adk` | Lists all running processes matching "adk". |
| `kill -9 <PID>` | Force-terminates a process by its PID. |
| `pkill -f "adk web"` | Kills all processes matching the pattern "adk web". |


### **8. ADK Starter Pack**

# Create with all defaults (project: my-agent, agent: adk_base, target: agent_engine)
uvx agent-starter-pack create -y

# Fully interactive mode
uvx agent-starter-pack create

# Quick prototype (no CI/CD, no Terraform)
uvx agent-starter-pack create my-prototype -p -d agent_engine

# Create a new project with specific name
uvx agent-starter-pack create my-agent-project

# Create with specific built-in agent
uvx agent-starter-pack create my-agent -a adk_base -d cloud_run

# Include data ingestion with specific datastore
uvx agent-starter-pack create my-rag-agent -a adk_base -i -ds cloud_sql -d cloud_run

# Create with custom region and CI/CD
uvx agent-starter-pack create my-agent -a template-url --region europe-west1 --cicd-runner github_actions

# In-folder creation (add to existing project)
uvx agent-starter-pack create my-agent -a adk@data-science --in-folder

# Customize agent directory name
uvx agent-starter-pack create my-agent -a adk_base --agent-directory chatbot

# Skip all prompts for automation
uvx agent-starter-pack create my-agent -a template-url -y --skip-checks