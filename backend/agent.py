from typing import Optional, Dict, Any, List, Tuple
from models import DashboardData, MetricKPI, MetricChart, DataPoint
from mcp_client import MCPClient
from prompts import SYSTEM_PROMPT
import logging
import os
import json
import re
import time
import asyncio
from functools import lru_cache
from mistralai import Mistral
from pydantic import ValidationError

log = logging.getLogger("agent")

class DashboardAgent:
    def __init__(self, mcp_client: MCPClient, mistral_api_key: str, model: str = "mistral-large-latest"):
        self.mcp_client = mcp_client
        self.mistral_api_key = mistral_api_key
        self.model = model
        self.client = Mistral(api_key=mistral_api_key)
        self.max_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "15"))
        self._cached_mistral_tools: Optional[List[Dict[str, Any]]] = None
        
        # In-memory caching
        self._dashboard_cache: Dict[str, Tuple[DashboardData, float, float]] = {}  # city -> (data, timestamp, ttl)
        self._cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour default
        self._max_cache_size = int(os.getenv("MAX_CACHE_SIZE", "100"))  # max cached cities

    async def initialize_tools(self) -> None:
        """Fetch and cache MCP tool definitions at startup."""
        log.info("Fetching MCP tools...")
        self._cached_mistral_tools = await self._convert_mcp_tools_to_mistral_format()
        log.info("Cached %d tools for Mistral", len(self._cached_mistral_tools))

    @lru_cache(maxsize=1)
    async def _convert_mcp_tools_to_mistral_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Mistral function calling format. Cached to avoid repeated conversions."""
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
            
            # Add parameters from tool definition (MCP uses inputSchema, some use parameters)
            schema = tool.get("inputSchema") or tool.get("parameters") or {}
            props = schema.get("properties", schema) if isinstance(schema, dict) else {}
            required_list = schema.get("required", []) if isinstance(schema, dict) else []

            for param_name, param_info in (props.items() if isinstance(props, dict) else []):
                param_type = "string"  # default
                if isinstance(param_info, dict):
                    if param_info.get("type") == "integer":
                        param_type = "integer"
                    elif param_info.get("type") == "number":
                        param_type = "number"
                    elif param_info.get("type") == "boolean":
                        param_type = "boolean"
                    mistral_tool["function"]["parameters"]["properties"][param_name] = {
                        "type": param_type,
                        "description": param_info.get("description", param_info.get("title", "")),
                    }
                if param_name in required_list:
                    mistral_tool["function"]["parameters"]["required"].append(param_name)
            
            mistral_tools.append(mistral_tool)
        
        return mistral_tools

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result."""
        log.info("MCP tool call: %s(%s)", tool_name, ", ".join(f"{k}={v!r}" for k, v in list(arguments.items())[:3]))
        result = await self.mcp_client.call_tool(tool_name, arguments)
        log.info("MCP tool %s returned %d chars", tool_name, len(result))
        return result

    def _clean_cache(self) -> None:
        """Clean up expired cache entries and enforce size limits."""
        current_time = time.time()
        expired_cities = []
        
        # Remove expired entries
        for city, (data, timestamp, ttl) in self._dashboard_cache.items():
            if current_time - timestamp > ttl:
                expired_cities.append(city)
        
        for city in expired_cities:
            self._dashboard_cache.pop(city, None)
        
        # Enforce size limit (FIFO eviction)
        if len(self._dashboard_cache) > self._max_cache_size:
            oldest_city = min(self._dashboard_cache.keys(), key=lambda k: self._dashboard_cache[k][1])
            self._dashboard_cache.pop(oldest_city, None)

    async def _parse_dashboard_response(self, response_text: str) -> DashboardData:
        """Parse the JSON response from Mistral into DashboardData."""
        try:
            # Strip markdown code fences if present (e.g. ```json ... ```)
            text = response_text.strip()
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if json_match:
                text = json_match.group(1).strip()
            response_data = json.loads(text)
            
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

    async def run_dashboard_agent(self, city: str) -> Tuple[DashboardData, int]:
        """
        Run the full agentic loop for a given city name.
        Returns a tuple of (DashboardData, iterations).
        """
        # Check cache first
        self._clean_cache()
        if city in self._dashboard_cache:
            cached_data, timestamp, ttl = self._dashboard_cache[city]
            log.info("Cache hit for city: %s", city)
            return (cached_data, 0)  # 0 iterations for cached results

        start_time = time.time()
        iterations = 0

        if self._cached_mistral_tools is None:
            raise RuntimeError("Agent tools not initialized. Call initialize_tools() at startup.")

        log.info("Starting agent for city: %s", city)

        # Initialize messages with system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Build a civic dashboard for: {city}"}
        ]

        # Agentic loop
        while iterations < self.max_iterations:
            iterations += 1
            log.info(
                "Iteration %d/%d - calling Mistral API (messages: %d)...",
                iterations, self.max_iterations, len(messages),
            )

            # Heartbeat: log every 5s while Mistral call is in progress (blocks in thread)
            async def heartbeat(n: int):
                for i in range(1, 61):  # up to 5 min
                    await asyncio.sleep(5)
                    log.info("Still waiting for Mistral (iteration %d)... %ds elapsed", n, i * 5)

            heartbeat_task = asyncio.create_task(heartbeat(iterations))
            try:
                # Run blocking Mistral call in thread so heartbeat can run
                mistral_start = time.time()
                response = await asyncio.to_thread(
                    self.client.chat.complete,
                    model=self.model,
                    messages=messages,
                    tools=self._cached_mistral_tools,
                    tool_choice="auto",
                    parallel_tool_calls=True,
                )
                mistral_elapsed = time.time() - mistral_start
                log.info("Mistral returned in %.2fs", mistral_elapsed)
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Add assistant response to messages
            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            has_tools = hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls
            has_content = bool(assistant_message.content)
            log.info("Mistral response: %s", "tool_calls" if has_tools else ("content (%d chars)" % len(assistant_message.content or "")))

            # Check if we have tool calls to execute
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                tool_names = [tc.function.name for tc in assistant_message.tool_calls]
                log.info("Mistral requested %d tool calls: %s", len(tool_names), tool_names)

                # Execute all MCP tool calls concurrently
                async def execute_one(tool_call):
                    log.info("Starting execute_one for %s", tool_call.id)
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Create a new MCPClient for each concurrent call to avoid server-side session hanging bug
                    temp_client = MCPClient(base_url=self.mcp_client.base_url)
                    try:
                        tool_result = await temp_client.call_tool(function_name, function_args)
                    finally:
                        await temp_client.close()
                        
                    log.info("Finished execute_one for %s", tool_call.id)
                    return (tool_call.id, function_name, tool_result)

                log.info("Gathering results...")
                try:
                    results = await asyncio.gather(
                        *[execute_one(tc) for tc in assistant_message.tool_calls]
                    )
                    log.info("Gather completed with %d results", len(results))
                except Exception as e:
                    log.exception("Gather failed: %s", e)
                    raise
                for tool_call_id, function_name, tool_result in results:
                    messages.append({
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result,
                        "tool_call_id": tool_call_id
                    })
                
                # Continue loop to let Mistral process tool results
                log.info("Continuing to next iteration after tool calls")
                continue
            
            # If no tool calls, check if we have a final response
            if assistant_message.content:
                try:
                    # Try to parse as JSON response
                    dashboard_data = await self._parse_dashboard_response(assistant_message.content)
                    duration_seconds = time.time() - start_time
                    log.info("Agent completed in %d iterations (%.2fs)", iterations, duration_seconds)
                    
                    # Cache the result
                    self._dashboard_cache[city] = (dashboard_data, time.time(), self._cache_ttl)
                    self._clean_cache()  # Clean up after adding new entry
                    
                    return (dashboard_data, iterations)
                except ValueError as e:
                    # If parsing fails, continue the conversation
                    log.warning("Failed to parse response: %s. Continuing conversation...", e)
                    messages.append({
                        "role": "user",
                        "content": "Please provide the response in the exact JSON format specified in the system prompt."
                    })
                    continue
        
        # If we reach max iterations without a valid response
        log.error("Agent failed after %d iterations", self.max_iterations)
        raise RuntimeError(f"Agent failed to complete after {self.max_iterations} iterations")
