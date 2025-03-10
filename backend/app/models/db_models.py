from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

from app.database import Base

class Simulation(Base):
    """模拟记录模型"""
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    environment_size = Column(Integer, default=500)
    num_hunters = Column(Integer, default=5)
    num_targets = Column(Integer, default=1)
    algorithm_type = Column(String(50), default="APF")
    max_steps = Column(Integer, default=1000)
    is_captured = Column(Boolean, default=False)
    step_count = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    capture_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 新增字段
    captured_targets_count = Column(Integer, default=0)
    escaped_targets_count = Column(Integer, default=0)
    total_targets_count = Column(Integer, default=0)
    obstacle_count = Column(Integer, default=0)
    escaped = Column(Boolean, default=False)
    escape_time = Column(Float, nullable=True)
    
    # 关联
    agents = relationship("Agent", back_populates="simulation", cascade="all, delete-orphan")
    snapshots = relationship("SimulationSnapshot", back_populates="simulation", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "environment_size": self.environment_size,
            "num_hunters": self.num_hunters,
            "num_targets": self.num_targets,
            "algorithm_type": self.algorithm_type,
            "max_steps": self.max_steps,
            "is_captured": self.is_captured,
            "step_count": self.step_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "capture_time": self.capture_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "captured_targets_count": self.captured_targets_count,
            "escaped_targets_count": self.escaped_targets_count,
            "total_targets_count": self.total_targets_count,
            "obstacle_count": self.obstacle_count,
            "escaped": self.escaped,
            "escape_time": self.escape_time
        }

class Agent(Base):
    """智能体记录模型"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), nullable=False)
    agent_id = Column(Integer, nullable=False)  # 模拟中的智能体ID
    type = Column(String(20), nullable=False)  # hunter 或 target
    start_position_x = Column(Float, nullable=False)
    start_position_y = Column(Float, nullable=False)
    velocity = Column(Float, default=1.0)
    vision_range = Column(Float, default=100.0)
    communication_range = Column(Float, default=150.0)
    
    # 关联
    simulation = relationship("Simulation", back_populates="agents")
    positions = relationship("AgentPosition", back_populates="agent", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "agent_id": self.agent_id,
            "type": self.type,
            "start_position": [self.start_position_x, self.start_position_y],
            "velocity": self.velocity,
            "vision_range": self.vision_range,
            "communication_range": self.communication_range
        }

class AgentPosition(Base):
    """智能体位置历史记录"""
    __tablename__ = "agent_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    step = Column(Integer, nullable=False)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 关联
    agent = relationship("Agent", back_populates="positions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "step": self.step,
            "position": [self.position_x, self.position_y],
            "timestamp": self.timestamp.isoformat()
        }

class SimulationSnapshot(Base):
    """模拟状态快照"""
    __tablename__ = "simulation_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), nullable=False)
    step = Column(Integer, nullable=False)
    hunters_state = Column(Text, nullable=False)  # 存储猎手状态的JSON
    targets_state = Column(Text, nullable=False)  # 存储目标状态的JSON
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 新增字段
    is_final = Column(Boolean, default=False)
    captured_targets_count = Column(Integer, default=0)
    escaped_targets_count = Column(Integer, default=0)
    
    # 关联
    simulation = relationship("Simulation", back_populates="snapshots")
    
    def to_dict(self):
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "step": self.step,
            "hunters_state": self.hunters_state,
            "targets_state": self.targets_state,
            "timestamp": self.timestamp.isoformat(),
            "is_final": self.is_final,
            "captured_targets_count": self.captured_targets_count,
            "escaped_targets_count": self.escaped_targets_count
        }