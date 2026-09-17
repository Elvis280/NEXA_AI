import asyncio
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing smoke test...")
    load_dotenv()
    
    # We must have PLAYWRIGHT_MCP_URL
    url = os.getenv("PLAYWRIGHT_MCP_URL")
    if not url:
        logger.error("PLAYWRIGHT_MCP_URL is not set.")
        return
        
    from app.mcp_client import mcp_manager
    
    try:
        tools = await mcp_manager.get_tools()
        logger.info(f"Connected successfully.")
        logger.info(f"Discovered {len(tools)} tools:")
        for t in tools:
            logger.info(f"- {t.name}: {t.description}")
            
    except Exception as e:
        logger.error(f"Failed to connect or discover tools: {e}")
        
    finally:
        await mcp_manager.cleanup()
        logger.info("Test complete")

if __name__ == "__main__":
    asyncio.run(main())
