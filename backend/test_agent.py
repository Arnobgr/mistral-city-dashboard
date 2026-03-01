import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from agent import DashboardAgent
from mcp_client import MCPClient
from models import DashboardData, MetricKPI, MetricChart, DataPoint
import json

# Test data
MOCK_CITY = "Paris"
MOCK_MISTRAL_API_KEY = "test_key_123"
MOCK_MCP_BASE_URL = "https://mcp.data.gouv.fr/mcp"

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = MagicMock(spec=MCPClient)
    client.list_tools = AsyncMock()
    client.call_tool = AsyncMock()
    client.close = AsyncMock()
    client.base_url = MOCK_MCP_BASE_URL  # Add base_url attribute
    return client

@pytest.fixture
def mock_mistral_client():
    """Create a mock Mistral client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    mock_message.tool_calls = []
    mock_message.content = json.dumps({
        "city": MOCK_CITY,
        "summary": "Test summary for Paris",
        "metrics": [
            {
                "id": "population",
                "title": "Population",
                "type": "kpi",
                "unit": "inhabitants",
                "source_dataset": "Population Data",
                "source_url": "https://example.com/population",
                "value": 2148000,
                "delta": 1.2,
                "delta_label": "vs 2020"
            },
            {
                "id": "unemployment_trend",
                "title": "Unemployment Trend",
                "type": "line_chart",
                "unit": "%",
                "source_dataset": "Employment Data",
                "source_url": "https://example.com/employment",
                "data": [
                    {"label": "2020", "value": 8.5},
                    {"label": "2021", "value": 7.8},
                    {"label": "2022", "value": 7.2}
                ]
            }
        ]
    })
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.complete = MagicMock(return_value=mock_response)
    
    return mock_client

@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools list."""
    return [
        {
            "name": "search_datasets",
            "description": "Search for datasets",
            "parameters": {
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "query_resource_data",
            "description": "Query data from a resource",
            "parameters": {
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "Resource ID"
                    },
                    "question": {
                        "type": "string",
                        "description": "Question to answer"
                    }
                },
                "required": ["resource_id", "question"]
            }
        }
    ]

def test_agent_initialization(mock_mcp_client):
    """Test agent initialization."""
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY,
        model="mistral-large-latest"
    )
    
    assert agent.mcp_client == mock_mcp_client
    assert agent.mistral_api_key == MOCK_MISTRAL_API_KEY
    assert agent.model == "mistral-large-latest"
    assert agent.max_iterations == 15  # Updated to match new default

def test_convert_mcp_tools_to_mistral_format(mock_mcp_client, mock_mcp_tools):
    """Test MCP to Mistral tools conversion."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )
    
    # Call the conversion method
    mistral_tools = agent._convert_mcp_tools_to_mistral_format()
    
    # Verify conversion
    assert len(mistral_tools) == 2
    assert mistral_tools[0]["type"] == "function"
    assert mistral_tools[0]["function"]["name"] == "search_datasets"
    assert "query" in mistral_tools[0]["function"]["parameters"]["properties"]
    assert "query" in mistral_tools[0]["function"]["parameters"]["required"]

def test_convert_mcp_tools_to_mistral_format(mock_mcp_client, mock_mcp_tools):
    """Test MCP to Mistral tools conversion."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )
    
    # Call the conversion method
    import asyncio
    mistral_tools = asyncio.run(agent._convert_mcp_tools_to_mistral_format())
    
    # Verify conversion
    assert len(mistral_tools) == 2
    assert mistral_tools[0]["type"] == "function"
    assert mistral_tools[0]["function"]["name"] == "search_datasets"
    assert "query" in mistral_tools[0]["function"]["parameters"]["properties"]
    assert "query" in mistral_tools[0]["function"]["parameters"]["required"]

@pytest.mark.asyncio
async def test_execute_mcp_tool(mock_mcp_client):
    """Test MCP tool execution."""
    mock_mcp_client.call_tool = AsyncMock(return_value='{"result": "test data"}')
    
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )
    
    result = await agent._execute_mcp_tool("search_datasets", {"query": "Paris"})
    assert result == '{"result": "test data"}'
    mock_mcp_client.call_tool.assert_awaited_once_with("search_datasets", {"query": "Paris"})

@pytest.mark.asyncio
async def test_parse_dashboard_response_valid():
    """Test parsing valid dashboard response."""
    mock_mcp_client = MagicMock()
    mock_mcp_client.list_tools = AsyncMock(return_value=[])
    
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )
    
    valid_json = json.dumps({
        "city": "Paris",
        "summary": "Test summary",
        "metrics": [
            {
                "id": "population",
                "title": "Population",
                "type": "kpi",
                "unit": "inhabitants",
                "source_dataset": "Population Data",
                "source_url": "https://example.com",
                "value": 2148000,
                "delta": 1.2,
                "delta_label": "vs 2020"
            }
        ]
    })
    
    result = await agent._parse_dashboard_response(valid_json)
    
    assert isinstance(result, DashboardData)
    assert result.city == "Paris"
    assert result.summary == "Test summary"
    assert len(result.metrics) == 1
    assert isinstance(result.metrics[0], MetricKPI)
    assert result.metrics[0].value == 2148000

@pytest.mark.asyncio
async def test_parse_dashboard_response_invalid():
    """Test parsing invalid dashboard response."""
    mock_mcp_client = MagicMock()
    mock_mcp_client.list_tools = AsyncMock(return_value=[])
    
    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )
    
    invalid_json = "Not a valid JSON"
    
    with pytest.raises(ValueError) as exc_info:
        await agent._parse_dashboard_response(invalid_json)
    
    assert "Failed to parse dashboard response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_parse_dashboard_response_rejects_malicious_source_url():
    """Agent rejects LLM response with javascript: URL (XSS prevention)."""
    mock_mcp_client = MagicMock()
    mock_mcp_client.list_tools = AsyncMock(return_value=[])

    agent = DashboardAgent(
        mcp_client=mock_mcp_client,
        mistral_api_key=MOCK_MISTRAL_API_KEY
    )

    malicious_json = json.dumps({
        "city": "Paris",
        "summary": "Test",
        "metrics": [
            {
                "id": "x",
                "title": "X",
                "type": "kpi",
                "unit": "",
                "source_dataset": "",
                "source_url": "javascript:alert(1)",
                "value": 1,
            }
        ]
    })

    with pytest.raises(ValueError) as exc_info:
        await agent._parse_dashboard_response(malicious_json)

    assert "Failed to parse dashboard response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_dashboard_agent_success(mock_mcp_client, mock_mistral_client, mock_mcp_tools):
    """Test successful agent execution."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    
    with patch('agent.Mistral', return_value=mock_mistral_client):
        agent = DashboardAgent(
            mcp_client=mock_mcp_client,
            mistral_api_key=MOCK_MISTRAL_API_KEY,
            model="mistral-large-latest"
        )
        
        # Initialize tools before running agent
        await agent.initialize_tools()
        
        result, iterations = await agent.run_dashboard_agent(MOCK_CITY)
        
        assert isinstance(result, DashboardData)
        assert result.city == MOCK_CITY
        assert len(result.metrics) == 2
        assert any(isinstance(metric, MetricKPI) for metric in result.metrics)
        assert any(isinstance(metric, MetricChart) for metric in result.metrics)

@pytest.mark.asyncio
async def test_run_dashboard_agent_with_tool_calls(mock_mcp_client, mock_mcp_tools):
    """Test agent execution with tool calls."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    mock_mcp_client.call_tool = AsyncMock(return_value='{"datasets": [{"id": "test"}]}')
    
    # Create mock Mistral client with tool calls
    mock_mistral_client = MagicMock()
    
    # First response with tool calls
    mock_message_with_tools = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search_datasets"
    mock_tool_call.function.arguments = json.dumps({"query": "Paris"})
    mock_tool_call.id = "tool_123"
    mock_message_with_tools.tool_calls = [mock_tool_call]
    mock_message_with_tools.content = ""
    
    mock_choice_with_tools = MagicMock()
    mock_choice_with_tools.message = mock_message_with_tools
    mock_response_with_tools = MagicMock()
    mock_response_with_tools.choices = [mock_choice_with_tools]
    
    # Second response with final answer
    mock_message_final = MagicMock()
    mock_message_final.tool_calls = []
    mock_message_final.content = json.dumps({
        "city": MOCK_CITY,
        "summary": "Test summary",
        "metrics": []
    })
    
    mock_choice_final = MagicMock()
    mock_choice_final.message = mock_message_final
    mock_response_final = MagicMock()
    mock_response_final.choices = [mock_choice_final]
    
    # Setup call sequence
    mock_mistral_client.chat.complete = MagicMock()
    mock_mistral_client.chat.complete.side_effect = [
        mock_response_with_tools,
        mock_response_final
    ]
    
    with patch('agent.Mistral', return_value=mock_mistral_client), \
         patch('agent.MCPClient', return_value=mock_mcp_client):
        agent = DashboardAgent(
            mcp_client=mock_mcp_client,
            mistral_api_key=MOCK_MISTRAL_API_KEY,
            model="mistral-large-latest"
        )
        
        # Initialize tools before running agent
        await agent.initialize_tools()
        
        result, iterations = await agent.run_dashboard_agent(MOCK_CITY)
        
        assert isinstance(result, DashboardData)
        assert result.city == MOCK_CITY
        # Verify tool was called
        mock_mcp_client.call_tool.assert_awaited_once_with("search_datasets", {"query": "Paris"})

@pytest.mark.asyncio
async def test_run_dashboard_agent_max_iterations(mock_mcp_client, mock_mcp_tools):
    """Test agent fails after max iterations."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    
    # Create mock Mistral client that never returns valid JSON
    mock_mistral_client = MagicMock()
    mock_message = MagicMock()
    mock_message.tool_calls = []
    mock_message.content = "Invalid response"
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    mock_mistral_client.chat.complete = MagicMock(return_value=mock_response)
    
    with patch('agent.Mistral', return_value=mock_mistral_client):
        agent = DashboardAgent(
            mcp_client=mock_mcp_client,
            mistral_api_key=MOCK_MISTRAL_API_KEY,
            model="mistral-large-latest"
        )
        agent.max_iterations = 2  # Set low for testing
        
        # Initialize tools before running agent
        await agent.initialize_tools()
        
        with pytest.raises(RuntimeError) as exc_info:
            await agent.run_dashboard_agent(MOCK_CITY)
        
        assert "Agent failed to complete after 2 iterations" in str(exc_info.value)

@pytest.mark.asyncio
async def test_dashboard_caching(mock_mcp_client, mock_mistral_client, mock_mcp_tools):
    """Test that dashboard results are cached properly."""
    mock_mcp_client.list_tools = AsyncMock(return_value=mock_mcp_tools)
    
    with patch('agent.Mistral', return_value=mock_mistral_client):
        agent = DashboardAgent(
            mcp_client=mock_mcp_client,
            mistral_api_key=MOCK_MISTRAL_API_KEY,
            model="mistral-large-latest"
        )
        agent._cache_ttl = 3600  # Set cache TTL for testing
        agent._max_cache_size = 100  # Set max cache size for testing
        
        # Initialize tools before running agent
        await agent.initialize_tools()
        
        # First call - should execute normally
        result1, iterations1 = await agent.run_dashboard_agent(MOCK_CITY)
        assert iterations1 > 0  # Should have actual iterations
        
        # Second call - should be cached
        result2, iterations2 = await agent.run_dashboard_agent(MOCK_CITY)
        assert iterations2 == 0  # Should be cached (0 iterations)
        assert result1.city == result2.city
        assert result1.summary == result2.summary

if __name__ == "__main__":
    pytest.main([__file__, "-v"])