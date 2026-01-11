from pathlib import Path
from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from agent.deerflow.config import load_yaml_config

def _get_llm_type_config_keys() -> dict[str, str]:
    """Get mapping of LLM types to their configuration keys."""
    return {
        "reasoning": "REASONING_MODEL",
        "basic": "BASIC_MODEL",
        "vision": "VISION_MODEL",
        "code": "CODE_MODEL",
    }

def _get_config_file_path()-> str:
    return str((Path (__file__).parent.parent.parent.parent.parent / "conf.yaml"))

def _create_llm_use_conf(llm_type, conf: Dict [str, Any])->BaseChatModel:

    llm_type_config_keys = _get_llm_type_config_keys()
    config_key = llm_type_config_keys.get(llm_type)
    llm_conf =  conf.get(config_key, {})
    return ChatOpenAI(**llm_conf)

def get_llm_by_type(llm_type: str):
    config = load_yaml_config(_get_config_file_path())
    llm = _create_llm_use_conf(llm_type, config)
    return llm



if __name__ == "__main__":
    path = _get_config_file_path()
    print(path)
    config = load_yaml_config(path)
    print(config)
