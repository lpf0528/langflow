from typing import Any, List
from fastapi.exceptions import HTTPException
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client


async def _get_tools_from_client_session(
    client_content_manager:Any, timeout_seconds:int=10
)->List:
    """从客户端会话中获取工具"""
    async with client_content_manager as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timeout_seconds) as session:
            await session.initialize()
            # https://github.com/modelcontextprotocol/python-sdk
            listed_tools = await session.list_tools()
            return listed_tools.tools


async def load_mcp_tools(    server_type: str,
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    url: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: Optional[int] = 30,  # Reasonable default timeout
    sse_read_timeout: Optional[int] = None,
):
    """加载MCP工具"""
    # {"transport":"stdio","name":"baidu-map","command":"npx","args":["-y","@baidumap/mcp-server-baidu-map"],"env":{"BAIDU_MAP_API_KEY":"xxx"}}
    if server_type == "stdio":
        if not command:
            raise HTTPException(status_code=400, detail="command is required")
        server_params = StdioServerParameters(
            transport=server_type,
            command=command,
            args=args,
            env=env,
        )
        return await _get_tools_from_client_session(stdio_client(server_params), timeout_seconds)
    elif server_type == "sse":
       pass
    elif server_type == "streamable_http":
        pass
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported server type: {server_type}"
        )