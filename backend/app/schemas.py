from pydantic import BaseModel, Field, field_serializer
from typing import List, Dict, Optional, Any
from datetime import datetime

# 基础模型
class AgentBase(BaseModel):
    position: List[float]
    velocity: float
    vision_range: float
    communication_range: float

class AgentCreate(AgentBase):
    agent_id: int
    type: str

class AgentResponse(AgentBase):
    id: int
    agent_id: int
    type: str
    history: Optional[List[List[float]]] = None

    class Config:
        from_attributes = True  # 使用新的V2命名

# 模拟相关模型
class SimulationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    environment_size: int = Field(500, description="环境大小")
    num_hunters: int = Field(5, description="猎手数量")
    num_targets: int = Field(1, description="目标数量")
    algorithm_type: str = Field("APF", description="算法类型: APF, CONSENSUS")
    max_steps: int = Field(1000, description="最大步数")

class SimulationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    environment_size: Optional[int] = None
    num_hunters: Optional[int] = None
    num_targets: Optional[int] = None
    algorithm_type: Optional[str] = None
    max_steps: Optional[int] = None

class SimulationList(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    num_hunters: int
    num_targets: int
    algorithm_type: str
    is_captured: bool
    step_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    # 添加日期时间序列化方法
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        # 如果已经是字符串，直接返回
        return value

class SimulationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    hunters: List[Dict[str, Any]]
    targets: List[Dict[str, Any]]
    environment_size: int
    algorithm_type: str
    step_count: int
    is_running: bool
    is_captured: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    capture_time: Optional[float] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

    # 添加日期时间序列化方法
    @field_serializer('created_at', 'updated_at', 'start_time', 'end_time')
    def serialize_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        # 如果已经是字符串，直接返回
        return value