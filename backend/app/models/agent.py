import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import math
import random
from collections import defaultdict

class Agent:
    """基础智能体类"""
    def __init__(self, agent_id: int, position: Tuple[float, float], 
                 velocity: float = 1.0, vision_range: float = 100.0, 
                 communication_range: float = 150.0):
        self.id = agent_id
        self.position = np.array(position, dtype=float)
        self.velocity = velocity
        self.vision_range = vision_range
        self.communication_range = communication_range
        self.neighbors = []
        self.history = [self.position.copy()]  # 存储轨迹
        
    def move(self, direction: np.ndarray, dt: float = 1.0):
        """按指定方向移动智能体"""
        # 确保总是有一些移动
        if np.linalg.norm(direction) < 0.001:
            # 如果方向向量太小，添加随机方向
            angle = random.uniform(0, 2 * math.pi)
            direction = np.array([math.cos(angle), math.sin(angle)]) * self.velocity
        
        if np.linalg.norm(direction) > 0:
            normalized_direction = direction / np.linalg.norm(direction)
            
            # 计划移动到的新位置
            planned_position = self.position + normalized_direction * self.velocity * dt
            
            # 边界检查
            if hasattr(self, 'environment_boundary') and self.environment_boundary is not None:
                try:
                    min_x, min_y, max_x, max_y = self.environment_boundary
                    planned_position[0] = max(min_x + 5, min(max_x - 5, planned_position[0]))
                    planned_position[1] = max(min_y + 5, min(max_y - 5, planned_position[1]))
                except (TypeError, ValueError):
                    # 如果解包失败，使用默认边界
                    planned_position[0] = max(0, min(500, planned_position[0]))
                    planned_position[1] = max(0, min(500, planned_position[1]))
            
            # 障碍物检查 - 使用多段检测确保不会穿过障碍物
            if hasattr(self, 'obstacles') and self.obstacles:
                # 前向路径检测 - 检查从当前位置到计划位置的整条路径
                path_is_clear = True
                collision_point = None
                collision_obstacle = None
                
                # 将路径分成10段进行检测
                for t in np.linspace(0, 1, 10):
                    check_position = self.position + t * (planned_position - self.position)
                    
                    for obstacle in self.obstacles:
                        obstacle_pos = np.array(obstacle['position'])
                        # 增加安全边界，确保不会太靠近障碍物
                        safe_radius = obstacle['radius'] + 5
                        
                        if np.linalg.norm(check_position - obstacle_pos) < safe_radius:
                            path_is_clear = False
                            collision_point = check_position
                            collision_obstacle = obstacle
                            break
                    
                    if not path_is_clear:
                        break
                
                if not path_is_clear and collision_obstacle:
                    # 如果路径被阻挡，计算切线方向移动
                    obstacle_pos = np.array(collision_obstacle['position'])
                    # 从障碍物中心到碰撞点的向量
                    from_obstacle = collision_point - obstacle_pos
                    if np.linalg.norm(from_obstacle) > 0:
                        from_obstacle = from_obstacle / np.linalg.norm(from_obstacle)
                        
                        # 计算切线方向（顺时针和逆时针两个选项）
                        tangent_cw = np.array([-from_obstacle[1], from_obstacle[0]])
                        tangent_ccw = np.array([from_obstacle[1], -from_obstacle[0]])
                        
                        # 选择更接近原始方向的切线
                        dot_cw = np.dot(normalized_direction, tangent_cw)
                        dot_ccw = np.dot(normalized_direction, tangent_ccw)
                        
                        tangent = tangent_cw if dot_cw > dot_ccw else tangent_ccw
                        
                        # 沿切线方向移动，但速度减半
                        safe_position = self.position + tangent * self.velocity * dt * 0.5
                        
                        # 再次检查安全位置是否与任何障碍物碰撞
                        safe_position_is_clear = True
                        for obstacle in self.obstacles:
                            obstacle_pos = np.array(obstacle['position'])
                            safe_radius = obstacle['radius'] + 5
                            
                            if np.linalg.norm(safe_position - obstacle_pos) < safe_radius:
                                safe_position_is_clear = False
                                break
                        
                        if safe_position_is_clear:
                            self.position = safe_position
                        else:
                            # 如果安全位置仍然不安全，只进行微小移动以避免卡死
                            # 远离最近的障碍物
                            closest_obstacle = min(self.obstacles, 
                                                key=lambda o: np.linalg.norm(np.array(o['position']) - self.position))
                            away_vector = self.position - np.array(closest_obstacle['position'])
                            if np.linalg.norm(away_vector) > 0:
                                away_vector = away_vector / np.linalg.norm(away_vector)
                                self.position = self.position + away_vector * 2  # 小步移动
                    else:
                        # 极端情况：如果正好在障碍物中心，随机移动
                        angle = random.uniform(0, 2 * math.pi)
                        random_direction = np.array([math.cos(angle), math.sin(angle)])
                        self.position = self.position + random_direction * 5
                else:
                    # 路径畅通，可以安全移动
                    self.position = planned_position
            else:
                # 没有障碍物，直接移动
                self.position = planned_position
                
            # 记录历史位置
            self.history.append(self.position.copy())
    
    def check_obstacle_collision(self, position, obstacle):
        """检查位置是否与障碍物碰撞"""
        # 假设障碍物为圆形
        obstacle_center = np.array(obstacle['position'])
        obstacle_radius = obstacle['radius']
        
        distance = np.linalg.norm(position - obstacle_center)
        return distance < obstacle_radius + 5  # 添加小缓冲区
    
    def calculate_reflection(self, direction, position, obstacle):
        """计算碰撞后的反射方向"""
        obstacle_center = np.array(obstacle['position'])
        
        # 计算从障碍物中心到智能体的向量
        normal = position - obstacle_center
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        else:
            # 如果恰好在中心，选择随机方向
            angle = random.uniform(0, 2 * math.pi)
            normal = np.array([math.cos(angle), math.sin(angle)])
        
        # 计算反射方向
        reflection = direction - 2 * np.dot(direction, normal) * normal
        return reflection
    
    def distance_to(self, other_agent) -> float:
        """计算与另一智能体的欧几里得距离"""
        return np.linalg.norm(self.position - other_agent.position)
    
    def can_see(self, other_agent) -> bool:
        """检查另一智能体是否在视野范围内"""
        if hasattr(self, 'obstacles') and self.obstacles:
            # 检查视线是否被障碍物阻挡
            return self.distance_to(other_agent) <= self.vision_range and not self.is_line_of_sight_blocked(other_agent)
        else:
            return self.distance_to(other_agent) <= self.vision_range
    
    def is_line_of_sight_blocked(self, other_agent) -> bool:
        """检查与其他智能体之间的视线是否被障碍物阻挡"""
        start = self.position
        end = other_agent.position
        direction = end - start
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            direction = direction / distance
        else:
            return False
        
        for obstacle in self.obstacles:
            obstacle_center = np.array(obstacle['position'])
            obstacle_radius = obstacle['radius']
            
            # 计算障碍物中心到线段的最近点
            t = np.dot(obstacle_center - start, direction)
            t = max(0, min(distance, t))
            nearest_point = start + t * direction
            
            # 检查最近点到障碍物中心的距离是否小于障碍物半径
            if np.linalg.norm(nearest_point - obstacle_center) < obstacle_radius:
                return True
        
        return False
    
    def can_communicate(self, other_agent) -> bool:
        """检查另一智能体是否在通信范围内"""
        return self.distance_to(other_agent) <= self.communication_range
    
    def update_neighbors(self, agents: List['Agent']):
        """优化版：更新通信范围内的邻居列表"""
        # 使用NumPy的向量化操作提高性能
        if len(agents) > 1:
            # 排除自己
            other_agents = [agent for agent in agents if agent.id != self.id]
            
            if not other_agents:
                self.neighbors = []
                return
                
            # 提取位置向量数组
            positions = np.array([agent.position for agent in other_agents])
            
            # 计算距离（向量化操作）
            distances = np.linalg.norm(positions - self.position, axis=1)
            
            # 找出在通信范围内的智能体
            in_range_indices = np.where(distances <= self.communication_range)[0]
            
            # 更新邻居列表
            self.neighbors = [other_agents[i] for i in in_range_indices]
        else:
            self.neighbors = []

    def to_dict(self) -> Dict:
        """转换为字典以便序列化"""
        return {
            "id": self.id,
            "position": self.position.tolist(),
            "velocity": self.velocity,
            "vision_range": self.vision_range,
            "communication_range": self.communication_range,
            "history": [pos.tolist() for pos in self.history],
        }

class HunterAgent(Agent):
    """猎手智能体类 - 状态机实现"""
    # 状态定义
    STATE_EXPLORE = 'explore'      # 初始探索阶段
    STATE_APPROACH = 'approach'    # 接近目标阶段 
    STATE_SURROUND = 'surround'    # 包围目标阶段
    STATE_CAPTURE = 'capture'      # 最终捕获阶段
    
    def __init__(self, agent_id: int, position: Tuple[float, float], 
                 velocity: float = 1.5, vision_range: float = 100.0, 
                 communication_range: float = 150.0,
                 learning_rate: float = 0.1, discount_factor: float = 0.9,
                 environment_boundary: Tuple[float, float, float, float] = None,
                 obstacles: List[Dict] = None):
        super().__init__(agent_id, position, velocity, vision_range, communication_range)
        self.target_position = None  # 目标位置的估计
        self.capture_range = 10.0    # 捕获范围
        
        # 设置环境边界
        self.environment_boundary = environment_boundary
        
        # 设置障碍物
        self.obstacles = obstacles or []
        
        # Q-learning参数
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table = defaultdict(lambda: defaultdict(float))  # Q值表
        self.last_state = None
        self.last_action = None
        
        # 目标轨迹预测
        self.target_history = []  # 存储目标的历史位置用于预测
        self.prediction_horizon = 10  # 预测未来多少步
        
        # 状态机变量
        self.state = self.STATE_EXPLORE
        self.assigned_position = None  # 分配的位置
        self.target_last_seen = None   # 上次看到目标的位置
        self.stalled_count = 0         # 卡住计数器
        
    def decide_action(self, target, all_hunters):
        """决策主函数，增强目标感知优先级"""
        # 更新目标位置
        self.target_position = target.position.copy()
        
        # 计算与目标的距离
        distance_to_target = np.linalg.norm(self.position - self.target_position)
        
        # 检测是否卡住
        if len(self.history) > 5:
            recent_movement = sum([np.linalg.norm(self.history[i+1] - self.history[i]) 
                            for i in range(len(self.history)-5, len(self.history)-1)])
            if recent_movement < 2.0:
                self.stalled_count += 1
            else:
                self.stalled_count = 0
                
        # 如果严重卡住，执行紧急移动
        if self.stalled_count > 10:
            self.stalled_count = 0
            # 卡住时，尝试朝向目标方向而非随机方向
            if distance_to_target > 10:
                direction = self.target_position - self.position
                if np.linalg.norm(direction) > 0:
                    return direction / np.linalg.norm(direction)
                    
            # 如果无法确定目标方向，再使用随机移动
            angle = random.uniform(0, 2 * math.pi)
            return np.array([math.cos(angle), math.sin(angle)])
        
        # 重要：改进状态转换逻辑，确保更积极地进入捕获状态
        # 距离判断更加宽松，确保能够有足够的机会进入捕获状态
        if distance_to_target <= self.capture_range * 2.0:  # 扩大触发捕获状态的距离范围
            self.state = self.STATE_CAPTURE
        elif distance_to_target <= self.capture_range * 4:
            self.state = self.STATE_SURROUND
        elif distance_to_target <= self.vision_range * 2:
            self.state = self.STATE_APPROACH
        else:
            self.state = self.STATE_EXPLORE
        
        # 根据状态执行对应行为
        if self.state == self.STATE_CAPTURE:
            return self.execute_capture(target)
        elif self.state == self.STATE_SURROUND:
            return self.execute_surround(target, all_hunters)
        elif self.state == self.STATE_APPROACH:
            return self.execute_approach(target)
        else:
            return self.execute_explore(target, all_hunters)
    
    def execute_capture(self, target):
        """执行捕获行为 - 直接冲向目标，忽略所有其他考虑"""
        # 临时增加速度以确保捕获
        self.velocity = 2.5  # 大幅增加速度
        
        # 直接冲向目标，不考虑其他猎手的排斥力
        direction = target.position - self.position
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            # 捕获阶段不受其他猎手影响，直线前进
            return direction / np.linalg.norm(direction) * 1.5  # 增加方向矢量强度
        return np.zeros(2)

    
    def execute_surround(self, target, all_hunters):
        """执行包围行为 - 根据猎手ID占据不同位置，减少互相排斥"""
        # 获取猎手数量和自己的ID
        hunter_count = len(all_hunters)
        my_index = next((i for i, h in enumerate(all_hunters) if h.id == self.id), 0)
        
        # 计算位置围成的圆上均匀分布的角度
        angle = (my_index / hunter_count) * 2 * math.pi
        
        # 计算包围半径 (略大于捕获范围)
        surround_radius = self.capture_range * 2
        
        # 计算目标位置
        target_pos = target.position
        ideal_x = target_pos[0] + surround_radius * math.cos(angle)
        ideal_y = target_pos[1] + surround_radius * math.sin(angle)
        ideal_position = np.array([ideal_x, ideal_y])
        
        # 计算前往理想位置的方向
        direction = ideal_position - self.position
        
        # 仅在接近障碍物时添加避障行为
        if self.obstacles:
            for obstacle in self.obstacles:
                obstacle_pos = np.array(obstacle['position'])
                distance = np.linalg.norm(self.position - obstacle_pos)
                
                if distance < obstacle['radius'] + 15:  # 仅当非常接近时
                    # 计算远离障碍物的方向
                    away_dir = self.position - obstacle_pos
                    if np.linalg.norm(away_dir) > 0:
                        away_dir = away_dir / np.linalg.norm(away_dir)
                        # 添加到方向中，权重随距离增加
                        weight = 1.0 - (distance / (obstacle['radius'] + 15))
                        direction += away_dir * weight * 5.0
        
        # 计算距离目标的距离
        distance_to_target = np.linalg.norm(self.position - target_pos)
        
        # 当非常接近目标时，减少猎手间的互相排斥
        if distance_to_target < self.capture_range * 3:
            # 减少这里的其他猎手互相排斥计算，专注于围捕
            # 保持原有方向不变，不再添加额外的排斥力
            pass
        else:
            # 远离目标时正常处理猎手间排斥
            for hunter in all_hunters:
                if hunter.id == self.id:
                    continue
                    
                # 计算与其他猎手的距离
                distance = np.linalg.norm(self.position - hunter.position)
                
                # 只在非常近时才考虑排斥
                if distance < 20:
                    repel_dir = self.position - hunter.position
                    if np.linalg.norm(repel_dir) > 0:
                        repel_dir = repel_dir / np.linalg.norm(repel_dir)
                        # 较弱的排斥力
                        direction += repel_dir * 0.3
        
        if np.linalg.norm(direction) > 0:
            return direction / np.linalg.norm(direction)
        return np.zeros(2)
    
    def execute_approach(self, target):
        """执行接近行为 - 直接向目标移动，避开障碍物"""
        # 基本方向是直接朝向目标
        direction = target.position - self.position
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        
        # 检查障碍物
        for obstacle in self.obstacles:
            obstacle_pos = np.array(obstacle['position'])
            obstacle_radius = obstacle['radius']
            
            # 检查是否在接近障碍物
            distance = np.linalg.norm(self.position - obstacle_pos)
            if distance < obstacle_radius + 30:
                # 计算当前前进方向与障碍物中心连线的角度
                to_obstacle = obstacle_pos - self.position
                if np.linalg.norm(to_obstacle) > 0:
                    to_obstacle = to_obstacle / np.linalg.norm(to_obstacle)
                
                dot_product = np.dot(direction, to_obstacle)
                
                # 如果朝向障碍物方向(夹角小于90度)，则需要避开
                if dot_product > 0:
                    # 计算垂直于障碍物方向的向量(两个方向)
                    perp1 = np.array([-to_obstacle[1], to_obstacle[0]])
                    perp2 = np.array([to_obstacle[1], -to_obstacle[0]])
                    
                    # 选择更接近原方向的那个
                    if np.dot(perp1, direction) > np.dot(perp2, direction):
                        avoid_dir = perp1
                    else:
                        avoid_dir = perp2
                    
                    # 避障力度随距离减小而增加
                    avoid_weight = 1.0 - (distance / (obstacle_radius + 30))
                    direction = direction * (1 - avoid_weight) + avoid_dir * avoid_weight
                    
                    # 归一化
                    if np.linalg.norm(direction) > 0:
                        direction = direction / np.linalg.norm(direction)
        
        return direction
    
    def execute_explore(self, target, all_hunters):
        """改进的探索行为 - 优先考虑目标位置，避免卡在边界"""
        # 获取所有猎手位置信息
        hunter_positions = [h.position for h in all_hunters if h.id != self.id]
        
        # 判断是否可以看到目标
        can_see_target = self.can_see(target)
        
        # 如果可以看到目标，直接向目标方向移动
        if can_see_target:
            direction = target.position - self.position
            if np.linalg.norm(direction) > 0:
                return direction / np.linalg.norm(direction)
        
        # 如果有位置已分配，检查是否需要更新
        if self.assigned_position is not None:
            # 如果已经接近分配位置，重新分配
            if np.linalg.norm(self.position - self.assigned_position) < 10:
                self.assigned_position = None
        
        # 如果没有分配位置，或需要更新
        if self.assigned_position is None:
            # 基于ID分配不同的探索区域
            if hasattr(self, 'environment_boundary') and self.environment_boundary:
                min_x, min_y, max_x, max_y = self.environment_boundary
                
                # 修改: 避免太靠近边界的区域，更集中在中心区域探索
                center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                width, height = max_x - min_x, max_y - min_y
                
                # 在中心区域按ID分配不同位置
                regions = [
                    (center_x - width * 0.25, center_y - height * 0.25),  # 中心偏左上
                    (center_x + width * 0.25, center_y - height * 0.25),  # 中心偏右上
                    (center_x - width * 0.25, center_y + height * 0.25),  # 中心偏左下
                    (center_x + width * 0.25, center_y + height * 0.25),  # 中心偏右下
                    (center_x, center_y)                                  # 中心
                ]
                
                region_index = self.id % len(regions)
                base_pos = np.array(regions[region_index])
                
                # 添加随机偏移，但确保不会太靠近边界
                max_offset = min(width, height) * 0.15
                offset = np.random.uniform(-max_offset, max_offset, 2)
                self.assigned_position = base_pos + offset
                
                # 确保在边界内且不太靠近边界
                margin = min(width, height) * 0.1
                self.assigned_position[0] = max(min_x + margin, min(max_x - margin, self.assigned_position[0]))
                self.assigned_position[1] = max(min_y + margin, min(max_y - margin, self.assigned_position[1]))
            else:
                # 默认环境大小500x500
                center_x, center_y = 250, 250
                regions = [
                    (center_x - 100, center_y - 100),
                    (center_x + 100, center_y - 100),
                    (center_x - 100, center_y + 100),
                    (center_x + 100, center_y + 100),
                    (center_x, center_y)
                ]
                region_index = self.id % len(regions)
                base_pos = np.array(regions[region_index])
                offset = np.random.uniform(-30, 30, 2)
                self.assigned_position = base_pos + offset
        
        # 前往分配的位置
        if self.assigned_position is not None:
            direction = self.assigned_position - self.position
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
            
            # 基本的障碍物避免
            for obstacle in self.obstacles:
                obstacle_pos = np.array(obstacle['position'])
                obstacle_radius = obstacle['radius']
                
                distance = np.linalg.norm(self.position - obstacle_pos)
                if distance < obstacle_radius + 20:
                    avoid_dir = self.position - obstacle_pos
                    if np.linalg.norm(avoid_dir) > 0:
                        avoid_dir = avoid_dir / np.linalg.norm(avoid_dir)
                        # 权重随距离减小而增加
                        weight = 1.0 - (distance / (obstacle_radius + 20))
                        direction = direction * (1 - weight) + avoid_dir * weight
                        if np.linalg.norm(direction) > 0:
                            direction = direction / np.linalg.norm(direction)
            
            return direction
        else:
            # 随机移动，但避免朝向边界
            if hasattr(self, 'environment_boundary') and self.environment_boundary:
                min_x, min_y, max_x, max_y = self.environment_boundary
                center = np.array([(min_x + max_x) / 2, (min_y + max_y) / 2])
                to_center = center - self.position
                
                # 如果靠近边界，偏向中心的随机移动
                if np.linalg.norm(to_center) > min(max_x - min_x, max_y - min_y) * 0.4:
                    if np.linalg.norm(to_center) > 0:
                        to_center = to_center / np.linalg.norm(to_center)
                        angle = random.uniform(-math.pi/4, math.pi/4)
                        rotation = np.array([[math.cos(angle), -math.sin(angle)], 
                                            [math.sin(angle), math.cos(angle)]])
                        return rotation.dot(to_center)
            
            angle = random.uniform(0, 2 * math.pi)
            return np.array([math.cos(angle), math.sin(angle)])
    
    def calculate_direction(self, target, all_hunters):
        """人工势场法入口 - 使用改进的人工势场法"""
        # 朝向目标的吸引力
        direction_to_target = target.position - self.position
        distance = np.linalg.norm(direction_to_target)
        
        if distance > 0:
            attraction = direction_to_target / distance
        else:
            attraction = np.zeros(2)
        
        # 来自其他猎手的排斥力
        repulsion = np.zeros(2)
        for hunter in all_hunters:
            if hunter.id == self.id:
                continue
                
            to_hunter = self.position - hunter.position
            hunter_distance = np.linalg.norm(to_hunter)
            
            if 0 < hunter_distance < 30:
                if hunter_distance > 0:
                    repulsion_dir = to_hunter / hunter_distance
                    
                    # 根据与目标的距离动态调整排斥力大小
                    # 离目标越近，排斥力越小，甚至为零
                    if distance < self.capture_range * 2.0:
                        repulsion_strength = 0.0  # 非常接近目标时完全消除排斥力
                    elif distance < self.capture_range * 4.0:
                        repulsion_strength = 0.1  # 接近目标时排斥力很小
                    else:
                        repulsion_strength = 1.0
                        
                    repulsion += repulsion_dir * (30 - hunter_distance) / 30 * repulsion_strength
        
        # 障碍物排斥力保持不变...
        obstacle_avoidance = np.zeros(2)
        for obstacle in self.obstacles:
            obstacle_pos = np.array(obstacle['position'])
            obstacle_radius = obstacle['radius']
            
            to_obstacle = self.position - obstacle_pos
            obstacle_distance = np.linalg.norm(to_obstacle)
            
            if obstacle_distance < obstacle_radius + 30:
                if obstacle_distance > 0:
                    obstacle_dir = to_obstacle / obstacle_distance
                    obstacle_avoidance += obstacle_dir * (obstacle_radius + 30 - obstacle_distance) / 30
        
        # 合并所有力 - 当靠近目标时增加吸引力权重
        if distance < self.capture_range * 2.0:
            attraction_weight = 3.0  # 非常靠近目标时大幅增加吸引力
            repulsion_weight = 0.0   # 完全消除排斥力
        else:
            attraction_weight = 1.5  # 正常吸引力
            repulsion_weight = 0.6   # 正常排斥力
            
        combined = attraction * attraction_weight + repulsion * repulsion_weight + obstacle_avoidance * 1.2
        
        if np.linalg.norm(combined) > 0:
            return combined / np.linalg.norm(combined)
        else:
            return attraction  # 默认返回朝向目标的方向
    
    def calculate_direction_advanced(self, target, all_hunters: List['HunterAgent']):
        """共识算法入口 - 使用状态机"""
        self.capture_range = 20.0  # 稍微增大捕获范围
        self.velocity = 1.8  # 稍微增加速度
        return self.decide_action(target, all_hunters)
    
    def encirclement_strategy(self, target, all_hunters: List['HunterAgent']):
        """包围策略入口 - 完全独特的包围行为"""        
        # 获取目标位置
        target_pos = target.position
        
        # 计算与目标的距离
        distance_to_target = np.linalg.norm(self.position - target_pos)
        
        # 如果非常接近目标，直接捕获
        if distance_to_target <= self.capture_range * 1.2:
            direction = target_pos - self.position
            if np.linalg.norm(direction) > 0:
                return direction / np.linalg.norm(direction)
            return np.zeros(2)
        
        # 包围策略: 猎手均匀分布在目标周围
        hunter_count = len(all_hunters)
        
        # 确定自己在猎手中的索引位置
        hunter_index = next((i for i, h in enumerate(all_hunters) if h.id == self.id), 0)
        
        # 基于目标移动方向的高级包围
        target_direction = np.zeros(2)
        if len(target.history) >= 3:
            target_direction = target.position - target.history[-3]
            if np.linalg.norm(target_direction) > 0:
                target_direction = target_direction / np.linalg.norm(target_direction)
        
        # 包围半径 - 根据猎手数量动态调整
        surround_radius = 40 + 5 * hunter_count
        
        # 特殊角色: 拦截者和包围者
        # 索引0的猎手负责在目标前方拦截，其他猎手负责包围
        if hunter_index == 0 and np.linalg.norm(target_direction) > 0.1:
            # 拦截者: 直接前往目标前方
            intercept_distance = 40
            intercept_pos = target_pos + target_direction * intercept_distance
            
            # 确保在环境范围内
            if hasattr(self, 'environment_boundary') and self.environment_boundary:
                min_x, min_y, max_x, max_y = self.environment_boundary
                intercept_pos[0] = max(min_x + 10, min(max_x - 10, intercept_pos[0]))
                intercept_pos[1] = max(min_y + 10, min(max_y - 10, intercept_pos[1]))
            
            # 计算方向
            intercept_dir = intercept_pos - self.position
            if np.linalg.norm(intercept_dir) > 0:
                intercept_dir = intercept_dir / np.linalg.norm(intercept_dir)
                
                # 避开障碍物
                for obstacle in self.obstacles:
                    obstacle_pos = np.array(obstacle['position'])
                    distance = np.linalg.norm(self.position - obstacle_pos)
                    if distance < obstacle['radius'] + 20:
                        away_dir = self.position - obstacle_pos
                        if np.linalg.norm(away_dir) > 0:
                            away_dir = away_dir / np.linalg.norm(away_dir)
                            weight = 1.0 - (distance / (obstacle['radius'] + 20))
                            intercept_dir = intercept_dir * (1 - weight) + away_dir * weight
                            if np.linalg.norm(intercept_dir) > 0:
                                intercept_dir = intercept_dir / np.linalg.norm(intercept_dir)
                
                return intercept_dir
        
        # 包围者: 在目标周围均匀分布
        # 计算围绕目标的角度
        base_angle = 0
        if np.linalg.norm(target_direction) > 0.1:
            base_angle = math.atan2(target_direction[1], target_direction[0])
        
        # 每个猎手的角度偏移
        angle_offset = 2 * math.pi / (hunter_count - 1 if hunter_count > 1 else 1)
        
        # 调整hunter_index确保跳过索引0的猎手
        adjusted_index = hunter_index if hunter_index > 0 else 1
        
        # 计算该猎手的理想角度
        hunter_angle = base_angle + adjusted_index * angle_offset
        
        # 计算理想位置
        ideal_x = target_pos[0] + surround_radius * math.cos(hunter_angle)
        ideal_y = target_pos[1] + surround_radius * math.sin(hunter_angle)
        ideal_position = np.array([ideal_x, ideal_y])
        
        # 确保位置在环境范围内
        if hasattr(self, 'environment_boundary') and self.environment_boundary:
            min_x, min_y, max_x, max_y = self.environment_boundary
            ideal_position[0] = max(min_x + 10, min(max_x - 10, ideal_position[0]))
            ideal_position[1] = max(min_y + 10, min(max_y - 10, ideal_position[1]))
        
        # 计算前往理想位置的方向
        direction = ideal_position - self.position
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        
        # 避开障碍物
        for obstacle in self.obstacles:
            obstacle_pos = np.array(obstacle['position'])
            distance = np.linalg.norm(self.position - obstacle_pos)
            if distance < obstacle['radius'] + 20:
                away_dir = self.position - obstacle_pos
                if np.linalg.norm(away_dir) > 0:
                    away_dir = away_dir / np.linalg.norm(away_dir)
                    weight = 1.0 - (distance / (obstacle['radius'] + 20))
                    direction = direction * (1 - weight) + away_dir * weight
                    if np.linalg.norm(direction) > 0:
                        direction = direction / np.linalg.norm(direction)
        
        return direction
    
    def predict_target_movement(self, target):
        """预测目标未来位置"""
        if len(target.history) < 3:
            return target.position
        
        # 获取最近三个位置
        positions = [np.array(pos) for pos in target.history[-3:]]
        
        # 计算速度向量
        velocity1 = positions[1] - positions[0]
        velocity2 = positions[2] - positions[1]
        
        # 计算平均速度和加速度
        avg_velocity = (velocity1 + velocity2) / 2
        acceleration = velocity2 - velocity1
        
        # 预测未来位置（使用物理公式：位置 + 速度*时间 + 0.5*加速度*时间^2）
        prediction_time = 1.5  # 预测1.5步
        future_position = positions[2] + avg_velocity * prediction_time + 0.5 * acceleration * prediction_time * prediction_time
        
        return future_position
    
    def can_capture(self, target) -> bool:
        """检查是否可以捕获目标"""
        # 简化捕获判断，只要在捕获范围内即可
        capture_threshold = self.capture_range * 1.5  # 增加50%的判断余量
        return self.distance_to(target) <= capture_threshold

class TargetAgent(Agent):
    """目标智能体类，支持多目标协作逃跑"""
    def __init__(self, agent_id: int, position: Tuple[float, float], 
                 velocity: float = 1.3, vision_range: float = 80.0,
                 environment_boundary: Tuple[float, float, float, float] = None,
                 obstacles: List[Dict] = None):
        super().__init__(agent_id, position, velocity, vision_range, 80.0)  # 目标有通信能力，范围80
        
        # 设置环境边界
        self.environment_boundary = environment_boundary
        
        # 设置障碍物
        self.obstacles = obstacles or []
        
        # 逃避策略参数
        self.memory_duration = 70  # 记忆持续时间（步数）
        self.hunter_memory = {}    # 记忆看到的猎手
        self.fear_factor = 2.0     # 恐惧因子，影响逃跑力度
        self.exploration_factor = 0.2  # 探索因子
        self.last_direction = None  # 记录上一次的移动方向
        self.direction_memory = 5   # 方向记忆强度
        self.stalled_count = 0      # 卡住计数器
        
        # 协作相关参数
        self.target_neighbors = [] # 附近的其他目标
        self.cooperation_weight = 0.4  # 协作权重
        self.last_seen_hunters = {}  # 上次看到的猎手信息
        self.danger_level = 0.0  # 危险级别
        
    def update_target_neighbors(self, targets):
        """更新附近的目标智能体"""
        # 排除自己
        other_targets = [t for t in targets if t.id != self.id]
        self.target_neighbors = [t for t in other_targets if self.can_communicate(t)]
        
    def calculate_direction_evasion(self, hunters: List[HunterAgent]) -> np.ndarray:
        """增强的逃离行为 - 支持多目标协作"""
        # 检测是否卡住
        if len(self.history) > 5:
            recent_movement = sum([np.linalg.norm(self.history[i+1] - self.history[i]) 
                                for i in range(len(self.history)-5, len(self.history)-1)])
            if recent_movement < 2.0:
                self.stalled_count += 1
            else:
                self.stalled_count = 0
                
        # 如果严重卡住，执行紧急移动
        if self.stalled_count > 8:
            self.stalled_count = 0
            angle = random.uniform(0, 2 * math.pi)
            self.last_direction = np.array([math.cos(angle), math.sin(angle)])
            return self.last_direction
        
        # 首先检查是否有猎手在视野范围内
        visible_hunters = [h for h in hunters if self.can_see(h)]
        
        # 更新上次看到的猎手信息
        for hunter in visible_hunters:
            self.last_seen_hunters[hunter.id] = {
                'position': hunter.position.copy(),
                'time': 0  # 刚刚看到
            }
        
        # 计算当前危险级别
        if visible_hunters:
            # 基于最近的猎手距离计算危险级别
            min_distance = min([np.linalg.norm(h.position - self.position) for h in visible_hunters])
            # 归一化危险级别，距离小于50时为高危险
            self.danger_level = max(0, 1 - (min_distance / 50))
        else:
            # 危险级别随时间衰减
            self.danger_level = max(0, self.danger_level - 0.05)
        
        # 如果有附近的目标，分享猎手信息
        if hasattr(self, 'target_neighbors') and self.target_neighbors:
            shared_hunters = {}
            
            # 获取邻居分享的猎手信息
            for neighbor in self.target_neighbors:
                if hasattr(neighbor, 'last_seen_hunters'):
                    for hunter_id, info in neighbor.last_seen_hunters.items():
                        if hunter_id not in shared_hunters or info['time'] < shared_hunters[hunter_id]['time']:
                            shared_hunters[hunter_id] = info
            
            # 更新自己的猎手记忆
            for hunter_id, info in shared_hunters.items():
                if hunter_id not in self.last_seen_hunters or self.last_seen_hunters[hunter_id]['time'] > info['time']:
                    self.last_seen_hunters[hunter_id] = info
        
        # 更新猎手记忆的时间
        for hunter_id in list(self.last_seen_hunters.keys()):
            self.last_seen_hunters[hunter_id]['time'] += 1
            # 移除过期记忆 (超过100步)
            if self.last_seen_hunters[hunter_id]['time'] > 100:
                del self.last_seen_hunters[hunter_id]
        
        # 基本逃离方向计算
        if visible_hunters:
            # 计算逃离方向 - 远离所有可见猎手的平均位置
            avg_hunter_pos = np.mean([h.position for h in visible_hunters], axis=0)
            direction = self.position - avg_hunter_pos
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
        else:
            # 没有直接可见的猎手，但可能有记忆中的猎手
            recent_hunters = [info for info in self.last_seen_hunters.values() if info['time'] < 30]
            
            if recent_hunters:
                # 基于记忆中的猎手位置计算逃离方向
                avg_pos = np.mean([info['position'] for info in recent_hunters], axis=0)
                memory_direction = self.position - avg_pos
                
                if np.linalg.norm(memory_direction) > 0:
                    memory_direction = memory_direction / np.linalg.norm(memory_direction)
                    
                    # 如果有上一次方向，融合记忆方向和上一次方向
                    if self.last_direction is not None:
                        memory_weight = 0.7 * (1 - min(30, max([info['time'] for info in recent_hunters])) / 30)
                        direction = memory_direction * memory_weight + self.last_direction * (1 - memory_weight)
                        if np.linalg.norm(direction) > 0:
                            direction = direction / np.linalg.norm(direction)
                    else:
                        direction = memory_direction
                else:
                    direction = self.get_random_or_previous_direction()
            else:
                direction = self.get_random_or_previous_direction()
        
        # 添加协作逃跑逻辑
        if hasattr(self, 'target_neighbors') and self.target_neighbors:
            # 如果有其他目标，考虑邻居的方向
            neighbor_directions = []
            neighbor_weights = []
            
            for neighbor in self.target_neighbors:
                if hasattr(neighbor, 'danger_level') and hasattr(neighbor, 'last_direction'):
                    # 如果邻居危险级别高且有移动方向
                    if neighbor.danger_level > 0.3 and neighbor.last_direction is not None:
                        # 计算距离权重
                        distance = np.linalg.norm(neighbor.position - self.position)
                        distance_weight = max(0, 1 - (distance / 80))
                        
                        # 计算危险权重
                        danger_weight = neighbor.danger_level
                        
                        # 计算最终权重
                        weight = distance_weight * danger_weight
                        
                        neighbor_directions.append(neighbor.last_direction)
                        neighbor_weights.append(weight)
            
            # 如果有有效的邻居方向
            if neighbor_directions:
                # 计算加权平均方向
                weighted_dir = np.zeros(2)
                total_weight = sum(neighbor_weights)
                
                if total_weight > 0:
                    for i, ndir in enumerate(neighbor_directions):
                        weighted_dir += ndir * (neighbor_weights[i] / total_weight)
                    
                    # 将邻居方向与自己的方向融合
                    coop_weight = self.cooperation_weight * min(1, total_weight)
                    final_direction = direction * (1 - coop_weight) + weighted_dir * coop_weight
                    
                    if np.linalg.norm(final_direction) > 0:
                        direction = final_direction / np.linalg.norm(final_direction)
        
        # 障碍物避开 - 同时考虑其他目标智能体作为"软障碍物"
        for obstacle in self.obstacles:
            obstacle_pos = np.array(obstacle['position'])
            obstacle_radius = obstacle['radius']
            
            distance = np.linalg.norm(self.position - obstacle_pos)
            # 只有非常接近障碍物时才调整
            if distance < obstacle_radius + 20:
                # 计算远离障碍物的方向
                away_dir = self.position - obstacle_pos
                if np.linalg.norm(away_dir) > 0:
                    away_dir = away_dir / np.linalg.norm(away_dir)
                    
                    # 障碍物影响权重随距离减小而增加
                    weight = 1.0
                    if distance > obstacle_radius:
                        weight = 1.0 - ((distance - obstacle_radius) / 20)
                    
                    # 完全近距离避让
                    if distance < obstacle_radius + 5:
                        direction = away_dir
                    else:
                        # 混合方向
                        direction = direction * (1 - weight) + away_dir * weight
                        if np.linalg.norm(direction) > 0:
                            direction = direction / np.linalg.norm(direction)
        
        # 避免与其他目标过于接近
        if hasattr(self, 'target_neighbors') and self.target_neighbors:
            for neighbor in self.target_neighbors:
                dist = np.linalg.norm(self.position - neighbor.position)
                if dist < 15:  # 目标之间保持一定距离
                    away_dir = self.position - neighbor.position
                    if np.linalg.norm(away_dir) > 0:
                        away_dir = away_dir / np.linalg.norm(away_dir)
                        # 计算权重
                        weight = 0.7 * (1 - dist / 15)
                        # 混合方向
                        direction = direction * (1 - weight) + away_dir * weight
                        if np.linalg.norm(direction) > 0:
                            direction = direction / np.linalg.norm(direction)
        
        # 记住上一次的方向
        self.last_direction = direction
        
        return direction
    
    def get_random_or_previous_direction(self):
        """获取随机方向或保持上一次的方向"""
        if self.last_direction is None or random.random() < 0.1:
            angle = random.uniform(0, 2 * math.pi)
            return np.array([math.cos(angle), math.sin(angle)])
        else:
            # 90%概率继续之前的方向
            return self.last_direction
    
    def update_hunter_memory(self, hunters: List[HunterAgent]):
        """更新猎手记忆"""
        # 减少所有记忆的剩余时间
        for hunter_id in self.hunter_memory:
            self.hunter_memory[hunter_id]['time_left'] -= 1
        
        # 移除过期记忆
        self.hunter_memory = {k: v for k, v in self.hunter_memory.items() if v['time_left'] > 0}
        
        # 更新可见猎手的记忆
        for hunter in hunters:
            if self.can_see(hunter):
                # 计算猎手速度，用于预测
                velocity = np.zeros(2)
                if len(hunter.history) > 1:
                    velocity = hunter.history[-1] - hunter.history[-2]
                
                self.hunter_memory[hunter.id] = {
                    'position': hunter.position.copy(),
                    'time_left': self.memory_duration,
                    'velocity': velocity
                }