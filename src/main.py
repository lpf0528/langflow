from contextlib import asynccontextmanager
from typing import Any, List, cast
import json, logging
from fastapi import FastAPI
from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from fastapi.responses import StreamingResponse
from agent.deerflow.graph.builder import build_deerflow_graph
from agent.deerflow.utiils.json_utils import sanitize_args
from .apps.chat_request import ChatRequest
from uuid import uuid4
from alembic.config import Config
from alembic import command
from .apps.api import api_router
from .apps.common.config import settings

logger = logging.getLogger(__name__)
memory = MemorySaver()
graph = build_deerflow_graph(checkpointer=memory)



def run_migrations():
    # 使用 Alembic 库来进行数据库迁移操作。
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager # 异步上下文管理器
async def lifespan(app: FastAPI):
    # 应用启动时执行
    # run_migrations()
    yield
    print("应用关闭")


app = FastAPI(
    lifespan=lifespan, # 生命周期管理
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.post('/api/chat/stream')
async def stream_chat(request: ChatRequest):
    thread_id = request.thread_id
    if thread_id == "__default__":
        thread_id = str(uuid4())
    return StreamingResponse(_astream_workflow_generator(
        request.model_dump()["messages"],
        thread_id,
        request.enable_clarification
    ), media_type="text/event-stream")


async def _astream_workflow_generator(messages: List[dict],thread_id:str,enable_clarification:bool):
    workflow_input={
        "messages": messages,
        "enable_clarification": enable_clarification
    }
    workflow_config={
        "thread_id": thread_id
    }
    # 流式调用图
    async for event in _stream_graph_events(
        graph, workflow_input, workflow_config, thread_id
    ):
        yield event

def _make_event(event_type:str, data: dict[str, Any]):
    if data.get('content') =='':
        data.pop('content')
    json_data = json.dumps(data, ensure_ascii=False)
    # TODO:完成原因
    # finish_reason = json_data.get('finish_reason', '')
    return f'event: {event_type}\ndata: {json_data}\n\n'


def _create_event_stream_message(message_chunk, message_metadata, thread_id, agent_name):
    content = message_chunk.content
    event_stream_message = {
        "thread_id": thread_id,
        "agent": agent_name,
        'id': message_chunk.id,
        'role':'assistant',
        'checkpoint_ns': message_metadata.get('checkpoint_ns', ''),
        'langgraph_node': message_metadata.get('langgraph_node', ''),
        'langgraph_path': message_metadata.get('langgraph_path', ''),
        'langgraph_step': message_metadata.get('langgraph_step', ''),
        "content": content
    }
    # TODO: reasoning_content
    # 解释完成原因
    if message_chunk.response_metadata.get('finish_reason', None):
        event_stream_message['finish_reason'] = message_chunk.response_metadata.get('finish_reason', '')


    return event_stream_message


def _get_agent_name(agent, message_metadata):
    agent_name = 'unknown'
    if agent and len(agent) > 0: 
        # TODO
        agent_name = agent[0]
    else: 
        agent_name = message_metadata.get('langgraph_node', 'unknown')

    return agent_name

async def _process_message_chunk(message_chunk: BaseMessage, message_metadata: dict[str, Any], thread_id, agent):
    # 处理消息块
    # TODO 空的
    agent_name = _get_agent_name(agent, message_metadata)
    # 构建基础消息字段
    event_stream_message = _create_event_stream_message(message_chunk, message_metadata, thread_id, agent_name)
    if isinstance(message_chunk, ToolMessage):
        raise ValueError("TODO: 处理工具消息")

    if isinstance(message_chunk, AIMessageChunk):
        if message_chunk.tool_calls:
            raise ValueError("TODO: 处理工具调用")
        if message_chunk.tool_call_chunks: # 工具调用参数块
            chunks_count = len(message_chunk.tool_call_chunks)
            processed_chunks = _process_tool_call_chunks(
                message_chunk.tool_call_chunks
            )
            event_stream_message['tool_call_chunks'] = processed_chunks
            yield _make_event('tool_call_chunks', event_stream_message)

        else: # 澄清式的直接回复
            yield _make_event('message_chunk', event_stream_message)

def _process_tool_call_chunks(tool_call_chunks: List[AIMessageChunk]):
    if not tool_call_chunks:
        return []
    chunks = []
    chunk_by_index = {} # 按索引分组块以处理流积累
    for chunk in tool_call_chunks:
        index = chunk.get('index')
        chunk_id = chunk.get('id', '')


        if index is not None:
            if index not in chunk_by_index:
                chunk_by_index[index] = {
                    'name':'',
                    'args':'',
                    'id':chunk_id,
                    'index':index,
                    'type': chunk.get('type', ''),
                }

            # 验证并积累工具名称
            chunk_name = chunk.get('name', '')
            if chunk_name:
                stored_name = chunk_by_index[index]['name']
                if stored_name and stored_name != chunk_name:
                    logger.warning(f"工具索引 {index} 名称不一致: {stored_name} != {chunk_name}")
                else:
                    chunk_by_index[index]['name'] = chunk_name
            if chunk_id and not chunk_by_index[index]['id']:
                chunk_by_index[index]['id'] = chunk_id
            if chunk.get('args'):
                chunk_by_index[index]['args'] += chunk.get('args', '')

        else:
            chunks.append({
                "name": chunk.get("name", ""),
                "args": sanitize_args(chunk.get("args", "")),
                "id": chunk.get("id", ""),
                "index": 0,
                "type": chunk.get("type", ""),
            })
    
    for index in sorted(chunk_by_index.keys()):
        chunk_data = chunk_by_index[index]
        chunk_data['args'] = sanitize_args(chunk_data['args'])
        chunks.append(chunk_data)
    
    return chunks

    
async def _stream_graph_events(graph: StateGraph, workflow_input, workflow_config, thread_id):

    # 返回消息流
    async for agent,stream_mode,event_data in graph.astream(
        workflow_input, 
        config=workflow_config, 
        stream_mode=['messages','updates'], 
        subgraphs=True
    ):
        print('------'*30)
        print(agent,stream_mode,event_data)

        # 系统提示词消息
        if isinstance(event_data, dict):
            if '__interrupt__' in event_data:
                # TODO: 中断时间
                raise ValueError(f'__interrupt__ 字段缺失: {event_data}')
            # 系统提示词
            continue

        # 2、工具消息
        # tuple[BaseMessage, dict[str, Any]] 表示我们期望 event_data 是一个包含两个元素的元组。
        # 第一个元素是 BaseMessage 类型，第二个元素是一个字典，字典的键是字符串类型，
        message_chunk, message_metadata = cast(tuple[BaseMessage, dict[str, Any]], event_data)
        # 处理消息块
        async for event in _process_message_chunk(message_chunk, message_metadata,thread_id ,agent):
            yield event
