import os
from dataclasses import dataclass, fields
from typing import Any

from langchain_core.runnables import RunnableConfig

# 如果设置kw_only=True，那么这个数据类的所有字段在实例化对象时都必须通过关键字参数来指定。这意味着，你不能仅通过位置参数来初始化数据类的实例。
@dataclass(kw_only=True)
class Configuration:
    # 强制使用web搜索
    enable_web_search: bool = True
    # 最大的搜索结果
    max_search_results: int = 3
    # 最大步数
    max_step_num: int = 3
    # 最大计划迭代次数
    max_plan_iterations: int = 3

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig=None):
        configuration = config.get('configuration', {})

        values: dict[str, Any] = {
            # f.init：只处理那些需要在初始化时设置的字段，也就是上面声明的字段
            f.name: os.environ.get(f.name.upper(), configuration.get(f.name))  for f in fields(cls) if f.init 
        }

        return cls(**{k:v for k,v in values.items() if v})
    