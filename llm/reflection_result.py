from typing import List, Literal

from pydantic import BaseModel, Field


class InsightLink(BaseModel):
    """insight 与 concept/emotion 的关联"""

    target: str  # 关联目标名称
    type: Literal["concept", "emotion"]
    weight: float = Field(ge=0.0, le=1.0)  # 关联强度 0.0-1.0


class ReflectionResult(BaseModel):
    """LLM reflect 输出结构"""

    insight: str  # 提取的洞察
    links: List[InsightLink] = Field(default_factory=list)
