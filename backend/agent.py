from typing import Optional
from models import DashboardData
from mcp_client import MCPClient
from prompts import SYSTEM_PROMPT
import os
import json
import time

class DashboardAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def run_dashboard_agent(self, city: str) -> DashboardData:
        """
        Run the full agentic loop for a given city name.
        Returns a structured DashboardData object.
        """
        start_time = time.time()
        iterations = 0
        
        # Initialize messages with system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Build a civic dashboard for: {city}"}
        ]

        # Placeholder for Mistral API call
        # This will be implemented in the next phase
        
        # For now, return a mock response
        mock_data = {
            "city": city,
            "summary": f"This is a mock summary for {city}.",
            "metrics": []
        }
        
        return DashboardData(**mock_data)
