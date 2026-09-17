from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .agent import run_agent
from .mcp_client import mcp_manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup on startup
    yield
    # Cleanup on shutdown
    await mcp_manager.cleanup()

app = FastAPI(title="Nexa AI Browser Automation", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class RunRequest(BaseModel):
    goal: str

class RunResponse(BaseModel):
    success: bool
    message: str
    steps: int

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/features")
async def features(request: Request):
    return templates.TemplateResponse("features.html", {"request": request})

@app.get("/contact")
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.post("/api/run", response_model=RunResponse)
async def api_run(req: RunRequest):
    try:
        result = await run_agent(req.goal)
        return RunResponse(
            success=True,
            message=result.get("output", "Task completed"),
            steps=result.get("steps", 0)
        )
    except Exception as e:
        return RunResponse(
            success=False,
            message=f"Error: {str(e)}",
            steps=0
        )
