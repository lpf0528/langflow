import yaml
import os
from typing import Any, Dict

def process_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    if not config:
        return {}
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = process_dict(value)
        # elif isinstance(value, str):
            # 替换环境变量中的值
            # result[key] = replace_env_vars(value)
        else:
            result[key] = value
    return result

_config_cache: Dict[str, Dict[str, Any]] = {}

def load_yaml_config(path: str) -> Dict[str, Any]:

    if not os.path.exists(path):
        raise {}

    # 检查缓存中是否已经存在配置
    if path in _config_cache:
        return _config_cache[path]

    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    
    config = process_dict(config)
    _config_cache[path] = config
    return config

