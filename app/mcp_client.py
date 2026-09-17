import os
import logging
from contextlib import AsyncExitStack
import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field
from typing import Any, Optional
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MCPManager:
    def __init__(self):
        self.session = None
        self.exit_stack = None

    async def connect(self):
        url = os.getenv("PLAYWRIGHT_MCP_URL")
        token = os.getenv("PLAYWRIGHT_MCP_TOKEN")
        
        if not url:
            logger.error("PLAYWRIGHT_MCP_URL is not configured")
            raise ValueError("PLAYWRIGHT_MCP_URL is not configured")
            
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            logger.warning("PLAYWRIGHT_MCP_TOKEN is not configured (proceeding without auth)")
            
        self.exit_stack = AsyncExitStack()
        
        try:
            logger.info("Connecting to Playwright MCP via Streamable HTTP...")
            # Manage HTTP client lifecycle via AsyncExitStack
            client = await self.exit_stack.enter_async_context(httpx2.AsyncClient(headers=headers, timeout=60.0))
            
            # Use streamable HTTP transport
            transport_ctx = streamable_http_client(url, http_client=client)
            
            read_stream, write_stream = await self.exit_stack.enter_async_context(transport_ctx)
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            await self.session.initialize()
            logger.info("MCP connection established and session initialized")
            
        except Exception as e:
            logger.error("Unable to connect to Playwright MCP server. Check PLAYWRIGHT_MCP_URL and ensure the Render service is running.")
            logger.error(f"Error details: {e}")
            await self.cleanup()
            raise RuntimeError(f"MCP initialization failure: {e}")
        
    async def get_tools(self):
        if not self.session:
            await self.connect()
            
        try:
            result = await self.session.list_tools()
            logger.info(f"Discovered {len(result.tools)} MCP tools")
            
            lc_tools = []
            for t in result.tools:
                lc_tools.append(self._create_lc_tool(t))
                
            return lc_tools
        except Exception as e:
            logger.error(f"Tool discovery failure: {e}")
            raise RuntimeError(f"Failed to list tools from MCP server: {e}")
            
    def _create_lc_tool(self, mcp_tool):
        async def _arun(**kwargs):
            try:
                res = await self.session.call_tool(mcp_tool.name, arguments=kwargs)
                if res.isError:
                    return f"Error executing tool {mcp_tool.name}: {res.content}"
                    
                outputs = []
                for content in res.content:
                    if content.type == "text":
                        outputs.append(content.text)
                    elif hasattr(content, "model_dump"):
                        # Extract structured content properly if available
                        dumped = content.model_dump()
                        if dumped.get("type") == "text":
                            outputs.append(dumped.get("text"))
                        else:
                            outputs.append(json.dumps(dumped, indent=2))
                    else:
                        outputs.append(f"[{content.type} received]")
                
                return "\n".join(outputs)
            except Exception as e:
                return f"Tool execution failed: {str(e)}"
            
        def _run(**kwargs):
            raise NotImplementedError("Only async execution is supported")
            
        # Convert JSON schema to Pydantic model
        schema = mcp_tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        fields = {}
        for prop_name, prop_info in properties.items():
            prop_type = Any
            ptype = prop_info.get("type")
            if ptype == "string":
                prop_type = str
            elif ptype == "integer":
                prop_type = int
            elif ptype == "number":
                prop_type = float
            elif ptype == "boolean":
                prop_type = bool
            elif ptype == "array":
                prop_type = list
            elif ptype == "object":
                prop_type = dict
                
            if prop_name not in required:
                prop_type = Optional[prop_type]
                default = None
            else:
                default = ...
                
            fields[prop_name] = (prop_type, Field(default=default, description=prop_info.get("description", "")))
            
        args_schema = create_model(f"{mcp_tool.name}Schema", **fields)
        
        return StructuredTool(
            name=mcp_tool.name,
            description=mcp_tool.description or mcp_tool.name,
            func=_run,
            coroutine=_arun,
            args_schema=args_schema
        )

    async def cleanup(self):
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = None
            self.session = None
            logger.info("MCP session closed")

# Global manager instance
mcp_manager = MCPManager()
