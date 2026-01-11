from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class StepType(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    PROCESSING = "processing"


class Step(BaseModel):
    need_search: bool = Field(..., description='必须为每个步骤明确设置。')
    title: str = Field(..., description='步骤的标题')
    description: str = Field(..., description='具体说明要收集哪些数据。')
    step_type: StepType = Field(..., description='指明步骤的性质。')
    execution_res: Optional[str] = Field(default=None, description='执行的结果')

class Plan(BaseModel):
    locale: str = Field(default='zh-CN', description='地区语言')
    has_enough_content: bool = Field(description='是否有足够的内容')
    thought: str = Field(default='', description='计划的思考过程')
    title: str = Field(description='计划的标题')
    steps: List[Step] = Field(default_factory=list, description='研究和处理步骤以获取更多背景信息。')
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "has_enough_context": False,
                    "thought": (
                        "To understand the current market trends in AI, we need to gather comprehensive information."
                    ),
                    "title": "AI Market Research Plan",
                    "steps": [
                        {
                            "need_search": True,
                            "title": "Current AI Market Analysis",
                            "description": (
                                "Collect data on market size, growth rates, major players, and investment trends in AI sector."
                            ),
                            "step_type": "research",
                        }
                    ],
                }
            ]
        }