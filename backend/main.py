from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from agent import DashboardAgent
from mcp_client import MCPClient
from models import DashboardData, DashboardResponse
import time

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://mcp.data.gouv.fr/mcp")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))

# Initialize MCP client and agent
mcp_client = MCPClient(base_url=MCP_BASE_URL)
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable is required")

agent = DashboardAgent(
    mcp_client=mcp_client,
    mistral_api_key=MISTRAL_API_KEY,
    model=MISTRAL_MODEL
)

# Pydantic models
class DashboardRequest(BaseModel):
    city: str = Field(..., min_length=1)

@app.post("/api/dashboard")
async def get_dashboard(request: DashboardRequest):
    start_time = time.time()
    
    try:
        # Run the agentic loop
        dashboard_data = await agent.run_dashboard_agent(request.city)
        duration_seconds = time.time() - start_time
        
        return DashboardResponse(
            data=dashboard_data,
            duration_seconds=duration_seconds,
            iterations=agent.max_iterations  # Note: we should track actual iterations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await mcp_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
