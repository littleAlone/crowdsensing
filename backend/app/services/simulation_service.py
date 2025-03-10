from typing import List, Dict, Tuple, Optional
import numpy as np
import time
import asyncio
import json
import logging
import random
import traceback

from app.models.agent import HunterAgent, TargetAgent
from app.database import SessionLocal
import datetime  
from app.models.db_models import SimulationSnapshot, Simulation

logger = logging.getLogger(__name__)

class SimulationService:
    """模拟服务类，管理多个模拟实例"""
    def __init__(self):
        self.simulations = {}
    
    def create_simulation(self, simulation_id: int, config: Dict) -> Dict:
        """创建新的模拟实例"""
        env_size = config.get("environment_size", 500)
        num_hunters = config.get("num_hunters", 5)
        num_targets = config.get("num_targets", 1)
        algorithm_type = config.get("algorithm_type", "APF")
        
        # 设置环境边界
        environment_boundary = (0, 0, env_size, env_size)
        
        # 创建猎手智能体
        hunters = []
        # 分散猎手在环境周围 - 围成圆形
        for i in range(num_hunters):
            angle = 2 * np.pi * i / num_hunters  # 均匀分布在圆周上
            distance = env_size * 0.4  # 距离中心的距离
            x = env_size / 2 + distance * np.cos(angle)
            y = env_size / 2 + distance * np.sin(angle)
            
            # 添加适当的随机性，避免完全对称
            x += np.random.uniform(-20, 20)
            y += np.random.uniform(-20, 20)
            
            # 确保在边界内
            x = max(10, min(env_size - 10, x))
            y = max(10, min(env_size - 10, y))
            
            hunter = HunterAgent(i, (x, y), vision_range=80.0)
            hunter.environment_boundary = environment_boundary
            hunters.append(hunter)
        
        # 创建目标智能体 - 放在中心位置
        targets = []
        for i in range(num_targets):
            x = env_size / 2 + np.random.uniform(-env_size/15, env_size/15)
            y = env_size / 2 + np.random.uniform(-env_size/15, env_size/15)
            target = TargetAgent(i + num_hunters, (x, y), vision_range=80.0)
            target.environment_boundary = environment_boundary
            targets.append(target)
        
        # 创建障碍物，确保不与智能体重叠
        num_obstacles = config.get("num_obstacles", 3)  # 默认3个障碍物
        obstacles = self.generate_obstacles(env_size, num_obstacles, hunters, targets)
        
        # 创建模拟对象
        new_simulation = {
            "id": simulation_id,
            "config": config,
            "hunters": hunters,
            "targets": targets,
            "obstacles": obstacles,
            "environment_size": env_size,
            "algorithm_type": algorithm_type,
            "step_count": 0,
            "is_running": False,
            "is_captured": False,
            "escaped": False,
            "start_time": None,
            "end_time": None,
            "capture_time": None,
            "escape_time": None,
            "max_steps": config.get("max_steps", 1000),
            "captured_targets_count": 0,
            "escaped_targets_count": 0,
            "total_targets_count": num_targets
        }
        
        # 设置障碍物
        for hunter in hunters:
            hunter.obstacles = obstacles
        for target in targets:
            target.obstacles = obstacles
        
        self.simulations[simulation_id] = new_simulation
        
        return self._simulation_to_dict(new_simulation)
    
    def generate_obstacles(self, env_size, num_obstacles, hunters=None, targets=None) -> List[Dict]:
        """
        生成静态障碍物，支持传入字典或Agent对象
        
        Args:
            env_size: 环境大小
            num_obstacles: 障碍物数量
            hunters: 猎手列表（可以是Agent对象或字典）
            targets: 目标列表（可以是Agent对象或字典）
        """
        obstacles = []
        num_obstacles = min(num_obstacles, 8)
        
        # 中心和边缘区域设置
        center_radius = env_size / 6
        center_x, center_y = env_size / 2, env_size / 2
        min_radius = env_size / 25
        max_radius = env_size / 12
        
        # 处理智能体位置（支持字典格式和Agent对象格式）
        agent_positions = []
        if hunters:
            for hunter in hunters:
                if hasattr(hunter, 'position'):
                    agent_positions.append(hunter.position)  # Agent对象
                elif isinstance(hunter, dict) and 'position' in hunter:
                    agent_positions.append(hunter['position'])  # 字典格式
        
        if targets:
            for target in targets:
                if hasattr(target, 'position'):
                    agent_positions.append(target.position)  # Agent对象
                elif isinstance(target, dict) and 'position' in target:
                    agent_positions.append(target['position'])  # 字典格式
        
        # 安全距离设置
        agent_safe_distance = max_radius + 25
        
        # 生成障碍物的主循环
        attempts = 0
        max_attempts = 200
        
        while len(obstacles) < num_obstacles and attempts < max_attempts:
            attempts += 1
            radius = np.random.uniform(min_radius, max_radius)
            edge_buffer = radius + 10
            
            # 在有效区域内生成位置
            x = np.random.uniform(edge_buffer, env_size - edge_buffer)
            y = np.random.uniform(edge_buffer, env_size - edge_buffer)
            
            # 中心区域检查
            if np.sqrt((x - center_x)**2 + (y - center_y)**2) < center_radius:
                continue
            
            # 障碍物重叠检查
            if any(np.sqrt((x - obs['position'][0])**2 + (y - obs['position'][1])**2) < 
                radius + obs['radius'] + 20 for obs in obstacles):
                continue
            
            # 与智能体重叠检查
            if any(np.sqrt((x - pos[0])**2 + (y - pos[1])**2) < 
                radius + agent_safe_distance for pos in agent_positions):
                continue
            
            # 通过检查，添加障碍物
            obstacles.append({
                'position': [x, y],
                'radius': radius,
                'type': 'circle'
            })
        
        logger.info(f"生成了{len(obstacles)}个障碍物")
        return obstacles
    
    def start_simulation(self, simulation_id: int) -> Dict:
        """启动模拟"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        simulation = self.simulations[simulation_id]
        simulation["is_running"] = True
        simulation["start_time"] = time.time()
        return self._simulation_to_dict(simulation)
    
    def stop_simulation(self, simulation_id: int) -> Dict:
        """停止模拟"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        simulation = self.simulations[simulation_id]
        simulation["is_running"] = False
        
        if simulation["is_captured"]:
            simulation["end_time"] = time.time()
            simulation["capture_time"] = simulation["end_time"] - simulation["start_time"]
        elif simulation["escaped"]:
            simulation["end_time"] = time.time()
            simulation["escape_time"] = simulation["end_time"] - simulation["start_time"]
        
        return self._simulation_to_dict(simulation)
    
    def reset_simulation(self, simulation_id: int) -> Dict:
        """重置模拟至初始状态"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        original_config = self.simulations[simulation_id]["config"]
        return self.create_simulation(simulation_id, original_config)
    
    async def step_simulation(self, simulation_id: int) -> Dict:
        """修改的模拟步进方法，支持多目标逐个捕获和目标协作"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        simulation = self.simulations[simulation_id]
        
        # 如果模拟已结束，不处理新消息
        if not simulation["is_running"]:
            return self._simulation_to_dict(simulation)
        
        hunters = simulation["hunters"]
        targets = simulation["targets"]
        algorithm_type = simulation["algorithm_type"]
        env_size = simulation["environment_size"]
        
        # 更新所有猎手的邻居
        for hunter in hunters:
            hunter.update_neighbors(hunters)
        
        # 更新所有目标的邻居（支持目标协作）
        for target in targets:
            if hasattr(target, 'update_target_neighbors'):
                target.update_target_neighbors(targets)
        
        # 检查是否有目标被捕获
        captured_targets = []
        for target in targets:
            is_captured = False
            
            # 检查是否有猎手捕获该目标
            for hunter in hunters:
                if np.linalg.norm(hunter.position - target.position) <= hunter.capture_range:
                    is_captured = True
                    logger.info(f"目标{target.id}被猎手{hunter.id}捕获")
                    break
                    
            # 如果这个目标被捕获，添加到捕获列表
            if is_captured:
                captured_targets.append(target)
        
        # 检查是否有目标到达边界逃脱成功
        escaped_targets = []
        border_margin = 10  # 边界安全距离
        
        for target in targets:
            # 检查是否接近边界
            if (target.position[0] <= border_margin or 
                target.position[0] >= env_size - border_margin or
                target.position[1] <= border_margin or
                target.position[1] >= env_size - border_margin):
                
                escaped_targets.append(target)
                logger.info(f"目标{target.id}成功逃脱到边界")
        
        # 处理被捕获的目标
        for target in captured_targets:
            # 从目标列表中移除
            if target in targets:  # 防止重复处理
                logger.info(f"从列表中移除目标{target.id}，当前剩余目标数: {len(targets)-1}")
                targets.remove(target)
                # 增加捕获计数
                if "captured_targets_count" not in simulation:
                    simulation["captured_targets_count"] = 0
                simulation["captured_targets_count"] += 1
                logger.info(f"已捕获目标数量: {simulation['captured_targets_count']}, 当前剩余目标数量: {len(targets)}")
        
        # 处理逃脱的目标
        for target in escaped_targets:
            # 避免重复处理
            if target in targets:
                targets.remove(target)
                # 增加逃脱计数
                if "escaped_targets_count" not in simulation:
                    simulation["escaped_targets_count"] = 0
                simulation["escaped_targets_count"] += 1
                logger.info(f"已逃脱目标数量: {simulation['escaped_targets_count']}")
        
        # 记录剩余目标数量
        remaining_targets = len(targets)
        logger.info(f"当前步骤后剩余目标数量: {remaining_targets}, 已捕获: {simulation.get('captured_targets_count', 0)}, 已逃脱: {simulation.get('escaped_targets_count', 0)}")
        
        # 没有剩余目标了，标记游戏结束
        if remaining_targets == 0:
            logger.info(f"所有目标已处理完毕，结束模拟, 总目标数: {simulation.get('total_targets_count', 0)}")
            simulation["is_running"] = False
            
            # 判断结束原因
            if simulation.get("captured_targets_count", 0) > 0 and simulation.get("escaped_targets_count", 0) == 0:
                # 全部被捕获
                simulation["is_captured"] = True
                simulation["end_time"] = time.time()
                simulation["capture_time"] = simulation["end_time"] - simulation["start_time"]
                logger.info(f"所有{simulation.get('captured_targets_count', 0)}个目标已被捕获")
                
                # 创建最终快照，包含完整状态信息
                try:
                    db = SessionLocal()
                    final_snapshot = SimulationSnapshot(
                        simulation_id=simulation_id,
                        step=simulation["step_count"],
                        hunters_state=json.dumps([h.to_dict() for h in simulation["hunters"]]),
                        targets_state=json.dumps([]),  # 空数组，因为所有目标都被捕获
                        is_final=True,  # 标记为最终快照
                        captured_targets_count=simulation.get("captured_targets_count", 0),
                        escaped_targets_count=simulation.get("escaped_targets_count", 0),
                        timestamp=datetime.datetime.utcnow()
                    )
                    db.add(final_snapshot)
                    
                    # 更新模拟记录
                    db_simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
                    if db_simulation:
                        db_simulation.is_captured = True
                        db_simulation.end_time = datetime.datetime.utcnow()
                        db_simulation.capture_time = (db_simulation.end_time - db_simulation.start_time).total_seconds() if db_simulation.start_time else 0
                        db_simulation.step_count = simulation["step_count"]
                        db_simulation.captured_targets_count = simulation.get("captured_targets_count", 0)
                        db_simulation.escaped_targets_count = simulation.get("escaped_targets_count", 0)
                        db_simulation.total_targets_count = simulation.get("total_targets_count", 0)
                    
                    db.commit()
                    db.close()
                except Exception as e:
                    logger.error(f"保存最终模拟状态失败: {str(e)}")
                    if 'db' in locals():
                        db.rollback()
                        db.close()
                    
            elif simulation.get("escaped_targets_count", 0) > 0 and simulation.get("captured_targets_count", 0) == 0:
                # 全部逃脱
                simulation["escaped"] = True
                simulation["end_time"] = time.time()
                simulation["escape_time"] = simulation["end_time"] - simulation["start_time"]
                logger.info(f"所有{simulation.get('escaped_targets_count', 0)}个目标已成功逃脱")
                
                # 类似上面，可以添加保存逃脱状态的代码
                
            else:
                # 部分捕获部分逃脱
                captured_count = simulation.get("captured_targets_count", 0)
                escaped_count = simulation.get("escaped_targets_count", 0)
                
                if captured_count >= escaped_count:
                    simulation["is_captured"] = True
                    simulation["end_time"] = time.time()
                    simulation["capture_time"] = simulation["end_time"] - simulation["start_time"]
                else:
                    simulation["escaped"] = True
                    simulation["end_time"] = time.time()
                    simulation["escape_time"] = simulation["end_time"] - simulation["start_time"]
                    
                logger.info(f"捕获{captured_count}个目标，逃脱{escaped_count}个目标")
                
                # 类似上面，可以添加保存混合状态的代码
                
            return self._simulation_to_dict(simulation)
        
        # 正常移动猎手
        for hunter in hunters:
            if not targets:  # 确保还有目标
                continue
                
            # 选择距离最近的目标
            nearest_target = min(targets, key=lambda t: np.linalg.norm(hunter.position - t.position))
            
            try:
                if algorithm_type == "APF":
                    direction = hunter.calculate_direction(nearest_target, hunters)
                elif algorithm_type == "CONSENSUS":
                    direction = hunter.calculate_direction_advanced(nearest_target, hunters)
                elif algorithm_type == "ENCIRCLEMENT":
                    direction = hunter.encirclement_strategy(nearest_target, hunters)
                else:
                    direction = hunter.calculate_direction(nearest_target, hunters)
                    
                # 确保direction不为None
                if direction is None:
                    direction = np.zeros(2)
                    
                hunter.move(direction)
            except Exception as e:
                logger.error(f"猎手移动计算错误: {str(e)}")
                continue
        
        # 移动目标
        for target in targets:
            try:
                direction = target.calculate_direction_evasion(hunters)
                # 确保direction不为None
                if direction is None:
                    direction = np.zeros(2)
                target.move(direction)
            except Exception as e:
                logger.error(f"目标移动计算错误: {str(e)}")
        
        # 更新步数
        simulation["step_count"] += 1
        
        # 检查是否达到最大步数
        if simulation["step_count"] >= simulation["max_steps"]:
            simulation["is_running"] = False
            logger.info(f"模拟 {simulation_id} 达到最大步数，仍有{len(targets)}个目标未捕获")
        
        # 控制模拟速度
        await asyncio.sleep(0.05)
        
        return self._simulation_to_dict(simulation)
    
    def get_simulation(self, simulation_id: int) -> Dict:
        """获取模拟当前状态"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        return self._simulation_to_dict(self.simulations[simulation_id])
    
    def get_all_simulations(self) -> List[Dict]:
        """获取所有模拟列表"""
        return [self._simulation_to_dict(sim) for sim in self.simulations.values()]
    
    def delete_simulation(self, simulation_id: int) -> None:
        """删除模拟"""
        if simulation_id in self.simulations:
            del self.simulations[simulation_id]
    
    def _simulation_to_dict(self, simulation) -> Dict:
        """将模拟对象转换为字典以便序列化"""
        # 确保hunters和targets是有效数组
        hunters = simulation["hunters"] if "hunters" in simulation else []
        targets = simulation["targets"] if "targets" in simulation else []
        result = {
            "id": simulation.get("id", 0),
            "config": simulation.get("config", {}),
            "hunters": [hunter.to_dict() for hunter in hunters],
            "targets": [target.to_dict() for target in targets],
            "environment_size": simulation.get("environment_size", 500),
            "algorithm_type": simulation.get("algorithm_type", "APF"),
            "step_count": simulation.get("step_count", 0),
            "is_running": simulation.get("is_running", False),
            "is_captured": simulation.get("is_captured", False),
            "escaped": simulation.get("escaped", False),
            "start_time": simulation.get("start_time"),
            "end_time": simulation.get("end_time"),
            "capture_time": simulation.get("capture_time"),
            "escape_time": simulation.get("escape_time"),
            "max_steps": simulation.get("max_steps", 1000),
            "obstacles": simulation.get("obstacles", []),
            "captured_targets_count": simulation.get("captured_targets_count", 0),
            "escaped_targets_count": simulation.get("escaped_targets_count", 0),
            "total_targets_count": simulation.get("total_targets_count", 
                                                simulation.get("captured_targets_count", 0) + 
                                                simulation.get("escaped_targets_count", 0) + 
                                                len(targets)),
            "remaining_targets_count": len(targets)
        }
        return result
    
    def update_simulation_obstacles(self, simulation_id: int, obstacles: List[Dict]) -> Dict:
        """更新模拟的障碍物"""
        if simulation_id not in self.simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        simulation = self.simulations[simulation_id]
        simulation["obstacles"] = obstacles
        
        # 更新猎手和目标智能体的障碍物引用
        for hunter in simulation["hunters"]:
            hunter.obstacles = obstacles
            # 确保环境边界仍然设置
            if not hasattr(hunter, 'environment_boundary') or hunter.environment_boundary is None:
                hunter.environment_boundary = (0, 0, simulation["environment_size"], simulation["environment_size"])
            
        for target in simulation["targets"]:
            target.obstacles = obstacles
            # 确保环境边界仍然设置
            if not hasattr(target, 'environment_boundary') or target.environment_boundary is None:
                target.environment_boundary = (0, 0, simulation["environment_size"], simulation["environment_size"])
            
        return self._simulation_to_dict(simulation)