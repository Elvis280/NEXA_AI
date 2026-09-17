import os
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field
from typing import Any, Optional

class MCPManager:
    def __init__(self):
        self.session = None
        self.exit_stack = None

    async def connect(self):
        url = os.getenv("PLAYWRIGHT_MCP_URL")
        token = os.getenv("PLAYWRIGHT_MCP_TOKEN")
        
        if not url:
            raise ValueError("PLAYWRIGHT_MCP_URL is required")
            
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        self.exit_stack = AsyncExitStack()
        
        # Use SSE client for HTTP transport. If streamable HTTP is needed in the future,
        # the mcp SDK will provide a separate client context manager.
        transport_ctx = sse_client(url, headers=headers)
        
        # SSE client returns (read_stream, write_stream)
        read_stream, write_stream = await self.exit_stack.enter_async_context(transport_ctx)
        
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        
        await self.session.initialize()
        
    async def get_tools(self):
        if not self.session:
            await self.connect()
            
        result = await self.session.list_tools()
        
        lc_tools = []
        for t in result.tools:
            lc_tools.append(self._create_lc_tool(t))
            
        return lc_tools
        
    def _create_lc_tool(self, mcp_tool):
        async def _arun(**kwargs):
            res = await self.session.call_tool(mcp_tool.name, arguments=kwargs)
            texts = []
            for content in res.content:
                if content.type == "text":
                    texts.append(content.text)
                else:
                    texts.append(f"[{content.type} received]")
            return "\n".join(texts)
            
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

# Global manager instance
mcp_manager = MCPManager()
