from fastapi import APIRouter
from src.apps.mcp_server.mcp_schema import MCPServerMetadataRequest
from src.apps.mcp_server.mcp_utils import load_mcp_tools
from src.apps.common.deps import SessionDep
from src.apps.common.loader import get_bool_env
from fastapi.exceptions import HTTPException

router = APIRouter(tags=["system_mcp"], prefix="/mcp")


@router.post("/server/metadata")
async def mcp_server_metadata(session: SessionDep, request: MCPServerMetadataRequest):
    """获取MCP服务元数据"""
    # {"transport":"stdio","name":"baidu-map","command":"npx","args":["-y","@baidumap/mcp-server-baidu-map"],"env":{"BAIDU_MAP_API_KEY":"xxx"}}
    # 是否开启MCP服务配置：ENABLE_MCP_SERVER_CONFIGURATION
    if not get_bool_env("ENABLE_MCP_SERVER_CONFIGURATION", False):
        raise HTTPException(
            status_code=403,
            detail="MCP server configuration is disabled. Set ENABLE_MCP_SERVER_CONFIGURATION=true to enable MCP features.",
        )
    tools = await load_mcp_tools(
        server_type=request.transport,
        command=request.command,
        args=request.args,
        url=request.url,
        env=request.env,
        headers=request.headers,
        timeout_seconds=request.timeout_seconds,
        sse_read_timeout=request.sse_read_timeout,
    )
    return {"request": tools}
