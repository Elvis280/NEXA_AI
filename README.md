# Nexa AI Browser Automation

Nexa is a minimal, AI-powered browser automation agent. It uses a LangChain ReAct agent powered by Gemini to understand natural language goals and accomplish them by dynamically utilizing browser tools provided by a remote Playwright MCP server.

## Architecture

```text
Nexa FastAPI
 ↓
LangChain + Gemini
 ↓
MCP Client
 ↓
Streamable HTTP
 ↓
Render Playwright MCP
 ↓
Chromium
```

- **Nexa FastAPI**: Serves the Jinja2 UI and handles API requests. Nexa acts purely as an **MCP client** for browser automation; it does not host a custom `mcp_server.py`.
- **LangChain + Gemini**: The core reasoning agent that decides which browser actions to take.
- **MCP Client**: Connects securely to the remote Playwright MCP server to discover and execute browser tools using Streamable HTTP.
- **Render Playwright MCP**: A remotely deployed service that actually runs Playwright and Chromium to interact with the web.

## Local Setup

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

1. Clone the repository.
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Set up the environment variables (see below).

## Environment Variables

Create a `.env` file from `.env.example`:

- `GOOGLE_API_KEY`: Your Gemini API key (e.g., from Google AI Studio). Used by LangChain to power the agent.
- `PLAYWRIGHT_MCP_URL`: The URL of your remote Playwright MCP server (e.g., `https://your-service.onrender.com/mcp`).
- `PLAYWRIGHT_MCP_TOKEN`: The bearer authentication token required to securely access the remote MCP server.

*Note: Never expose the `PLAYWRIGHT_MCP_TOKEN` to the frontend.*

## Running Locally

To start the FastAPI server:

```bash
uv run uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`.

## MCP Setup

Nexa expects a **remote** Playwright MCP endpoint. The browser automation is not performed locally to keep the architecture portable and decoupled. Make sure your Playwright MCP service is running and accessible via the URL specified in your `.env`.

## Deployment

The application is structured cleanly for cloud deployment:
- **Backend/Agent**: Because LangChain agent runs can take 10-30 seconds, deploying the FastAPI app to **Render** (or another containerized environment) is strongly recommended over Vercel (which imposes a strict 10-second timeout on the hobby tier).
- **Browser Automation**: Deployed separately on Render as the Playwright MCP server.
