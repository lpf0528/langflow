from typing import Any, List, Union, cast
import json
from fastapi import FastAPI
from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from fastapi.responses import StreamingResponse
from agent.deerflow.graph.builder import build_deerflow_graph
from .chat_request import ChatRequest
from uuid import uuid4

app = FastAPI()

memory = MemorySaver()
graph = build_deerflow_graph(checkpointer=memory)

@app.post('/api/chat/stream')
async def stream_chat(request: ChatRequest):
    thread_id = request.thread_id
    if thread_id == "__default__":
        thread_id = str(uuid4())
    return StreamingResponse(_astream_workflow_generator(
        request.model_dump()["messages"],
        thread_id
    ), media_type="text/event-stream")


async def _astream_workflow_generator(messages: List[dict],thread_id):
    workflow_input={
        "messages": messages
    }
    workflow_config={
        "thread_id": thread_id
    }
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
        "agent_name": agent_name,
        'id': message_chunk.id,
        'role':'assistant',
        "content": content
    }
    return event_stream_message


def _get_agent_name(agent, message_metadata):
    agent_name = 'unknown'
    if agent and len(agent) > 1: # TODO
        agent_name = agent[0]
    return agent_name

async def _process_message_chunk(message_chunk: BaseMessage, message_metadata: dict[str, Any], thread_id, agent):
    agent_name = _get_agent_name(agent, message_metadata)
    event_stream_message = _create_event_stream_message(message_chunk, message_metadata, thread_id, agent_name)
    if isinstance(message_chunk, AIMessageChunk):
        # if message_chunk.tool_calls:
        #     pass
        if message_chunk.tool_call_chunks:
            chunks_count = len(message_chunk.tool_call_chunks)
            processed_chunks = _process_tool_call_chunks(
                message_chunk.tool_call_chunks
            )
            event_stream_message['tool_call_chunks'] = processed_chunks
            yield _make_event('tool_call_chunks', event_stream_message)

        else:
            yield _make_event('message_chunk', event_stream_message)

def _process_tool_call_chunks(tool_call_chunks: List[AIMessageChunk]):
    if not tool_call_chunks:
        return []
    
    
    
async def _stream_graph_events(graph: StateGraph, workflow_input, workflow_config, thread_id):
    async for agent,stream_mode,event_data in graph.astream(
        workflow_input, 
        config=workflow_config, 
        stream_mode=['messages','updates'], 
        subgraphs=True
    ):
        print(agent,stream_mode,event_data)

        # tuple[BaseMessage, dict[str, Any]] 表示我们期望 event_data 是一个包含两个元素的元组。
        # 第一个元素是 BaseMessage 类型，第二个元素是一个字典，字典的键是字符串类型，
        message_chunk, message_metadata = cast(tuple[BaseMessage, dict[str, Any]], event_data)
        async for event in _process_message_chunk(message_chunk, message_metadata,thread_id ,agent):
            yield event
