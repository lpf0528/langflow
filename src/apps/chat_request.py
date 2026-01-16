from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    type: str = Field(..., description="The type of content (text, image, etc.)")
    text: Optional[str] = Field(None, description="The text content if type is 'text'")
    image_url: Optional[str] = Field(
        None, description="The image URL if type is 'image'"
    )


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender (user or assistant)"
    )
    content: Union[str, List[ContentItem]] = Field(
        ...,
        description="The content of the message, either a string or a list of content items",
    )


class ChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = Field(
        [], description="History of messages between the user and the assistant"
    )
    thread_id: Optional[str] = Field(
        "__default__", description="A specific conversation identifier"
    )
    enable_clarification: Optional[bool] = Field(
        False, description="Whether to enable clarification questions"
    )
    mcp_settings: Optional[dict] = Field(
        None, description="MCP server settings for the conversation"
    )
