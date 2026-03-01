from typing import Optional, Dict, Any, List
from models import DashboardData, MetricKPI, MetricChart, DataPoint
from mcp_client import MCPClient
from prompts import SYSTEM_PROMPT
import os
import json
import time
from mistralai import Mistral
from pydantic import ValidationError

class DashboardAgent:
    def __init__(self, mcp_client: MCPClient, mistral_api_key: str, model: str = "mistral-large-latest"):
        self.mcp_client = mcp_client
        self.mistral_api_key = mistral_api_key
        self.model = model
        self.client = Mistral(api_key=mistral_api_key)
        self.max_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))

    async def _convert_mcp_tools_to_mistral_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Mistral function calling format."""
        mcp_tools = await self.mcp_client.list_tools()
        mistral_tools = []
        
        for tool in mcp_tools:
            mistral_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters from tool definition
            if "parameters" in tool:
                for param_name, param_info in tool["parameters"].items():
                    param_type = "string"  # default
                    if param_info.get("type") == "integer":
                        param_type = "integer"
                    elif param_info.get("type") == "number":
                        param_type = "number"
                    elif param_info.get("type") == "boolean":
                        param_type = "boolean"
                    
                    mistral_tool["function"]["parameters"]["properties"][param_name] = {
                        "type": param_type,
                        "description": param_info.get("description", "")
                    }
                    
                    if param_info.get("required", False):
                        mistral_tool["function"]["parameters"]["required"].append(param_name)
            
            mistral_tools.append(mistral_tool)
        
        return mistral_tools

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result."""
        result = await self.mcp_client.call_tool(tool_name, arguments)
        return result

    async def _parse_dashboard_response(self, response_text: str) -> DashboardData:
        """Parse the JSON response from Mistral into DashboardData."""
        try:
            response_data = json.loads(response_text)
            
            # Validate and convert metrics
            metrics = []
            for metric_data in response_data.get("metrics", []):
                if metric_data["type"] == "kpi":
                    metric = MetricKPI(
                        id=metric_data["id"],
                        title=metric_data["title"],
                        type="kpi",
                        unit=metric_data["unit"],
                        source_dataset=metric_data["source_dataset"],
                        source_url=metric_data["source_url"],
                        value=metric_data["value"],
                        delta=metric_data.get("delta"),
                        delta_label=metric_data.get("delta_label")
                    )
                else:  # line_chart or bar_chart
                    data_points = [
                        DataPoint(label=dp["label"], value=dp["value"])
                        for dp in metric_data.get("data", [])
                    ]
                    metric = MetricChart(
                        id=metric_data["id"],
                        title=metric_data["title"],
                        type=metric_data["type"],
                        unit=metric_data["unit"],
                        source_dataset=metric_data["source_dataset"],
                        source_url=metric_data["source_url"],
                        data=data_points
                    )
                metrics.append(metric)
            
            return DashboardData(
                city=response_data["city"],
                summary=response_data["summary"],
                metrics=metrics
            )
        except (json.JSONDecodeError, KeyError, ValidationError) as e:
            raise ValueError(f"Failed to parse dashboard response: {e}")

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
        
        # Convert MCP tools to Mistral format
        mistral_tools = await self._convert_mcp_tools_to_mistral_format()
        
        # Agentic loop
        while iterations < self.max_iterations:
            iterations += 1
            
            # Call Mistral API with tools
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                tools=mistral_tools,
                tool_choice="any",
                parallel_tool_calls=False,
            )
            
            # Add assistant response to messages
            assistant_message = response.choices[0].message
            messages.append(assistant_message)
            
            # Check if we have tool calls to execute
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the MCP tool
                    tool_result = await self._execute_mcp_tool(function_name, function_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result,
                        "tool_call_id": tool_call.id
                    })
                
                # Continue loop to let Mistral process tool results
                continue
            
            # If no tool calls, check if we have a final response
            if assistant_message.content:
                try:
                    # Try to parse as JSON response
                    dashboard_data = await self._parse_dashboard_response(assistant_message.content)
                    duration_seconds = time.time() - start_time
                    
                    print(f"Agent completed in {iterations} iterations ({duration_seconds:.2f}s)")
                    return dashboard_data
                except ValueError as e:
                    # If parsing fails, continue the conversation
                    print(f"Failed to parse response: {e}. Continuing conversation...")
                    messages.append({
                        "role": "user",
                        "content": "Please provide the response in the exact JSON format specified in the system prompt."
                    })
                    continue
        
        # If we reach max iterations without a valid response
        raise RuntimeError(f"Agent failed to complete after {self.max_iterations} iterations")
