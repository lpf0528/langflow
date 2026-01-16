from pydantic import BaseModel, Field
from typing import List, Optional


class MCPServerMetadataRequest(BaseModel):
    """
    example:
        {
        "mcpServers": {
            "baidu-map": {
            "command": "npx",
            "args": [
                "-y",
                "@baidumap/mcp-server-baidu-map"
            ],
            "env": {
                "BAIDU_MAP_API_KEY": "xxx"
            }
            }
        }
        }
    """

    # {"transport":"stdio","name":"baidu-map","command":"npx","args":["-y","@baidumap/mcp-server-baidu-map"],"env":{"BAIDU_MAP_API_KEY":"xxx"}}
    transport: str = Field(
        ..., description="MCP服务的链接类型，可选值：stdio、sse、streamable_http"
    )
    command: Optional[str] = Field(default=None, description="命令")
    args: Optional[List[str]] = Field(None, description="参数")
    url: Optional[str] = Field(None, description="URL")
    env: Optional[dict[str, str]] = Field(None, description="环境变量")
    headers: Optional[dict[str, str]] = Field(None, description="HTTP头")
    timeout_seconds: Optional[int] = Field(
        default=30, ge=1, le=3600, description="超时时间（秒）"
    )
    sse_read_timeout: Optional[int] = Field(
        default=60, ge=1, le=3600, description="SSE读取超时时间（秒）"
    )


# class MCPServerMetadataResponse(BaseModel):
