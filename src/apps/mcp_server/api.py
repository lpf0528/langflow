

from fastapi import APIRouter
from apps.system.schemas.mcp_schema import MCPServerMetadataRequest
from apps.common.deps import SessionDep

router = APIRouter(tags=["system_mcp"], prefix="/mcp")

@router.post('/server/metadata')
async def mcp_server_metadata(session: SessionDep, request: MCPServerMetadataRequest):
    """获取MCP服务元数据"""
    # {"transport":"stdio","name":"baidu-map","command":"npx","args":["-y","@baidumap/mcp-server-baidu-map"],"env":{"BAIDU_MAP_API_KEY":"xxx"}}
    # 是否开启MCP服务配置：ENABLE_MCP_SERVER_CONFIGURATION

    return {"request": request}
