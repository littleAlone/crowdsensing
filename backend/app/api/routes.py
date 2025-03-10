import random
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import websockets
import traceback

from app.database import get_db
from app.schemas import SimulationCreate, SimulationUpdate, SimulationResponse, SimulationList
from app.services.simulation_service import SimulationService
from app.models.db_models import Simulation, Agent, AgentPosition, SimulationSnapshot

import logging
logger = logging.getLogger(__name__)

# 创建自定义路由类以支持所有方法
class AllowAllMethodsRoute(APIRoute):
    def get_methods(self):
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# 首先创建 router 对象
router = APIRouter(route_class=AllowAllMethodsRoute)
simulation_service = SimulationService()

# 获取所有模拟列表
@router.get("/simulations/", response_model=List[SimulationList])
def get_simulations(db: Session = Depends(get_db)):
    """获取所有模拟列表"""
    try:
        simulations = db.query(Simulation).all()
        logger.info(f"成功获取{len(simulations)}个模拟")
        return simulations
    except Exception as e:
        logger.error(f"获取模拟列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模拟列表失败: {str(e)}")

# 创建新模拟
@router.post("/simulations/", response_model=SimulationResponse, status_code=201)
def create_simulation(simulation_create: SimulationCreate, db: Session = Depends(get_db)):
    """创建新的模拟"""
    try:
        logger.info(f"创建新模拟: {simulation_create.name}")
        # 创建新模拟记录
        db_simulation = Simulation(
            name=simulation_create.name,
            description=simulation_create.description,
            environment_size=simulation_create.environment_size,
            num_hunters=simulation_create.num_hunters,
            num_targets=simulation_create.num_targets,
            algorithm_type=simulation_create.algorithm_type,
            max_steps=simulation_create.max_steps,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 先保存数据库记录
        db.add(db_simulation)
        db.commit()
        db.refresh(db_simulation)
        
        # 构建配置对象
        config = {
            "environment_size": db_simulation.environment_size,
            "num_hunters": db_simulation.num_hunters,
            "num_targets": db_simulation.num_targets,
            "algorithm_type": db_simulation.algorithm_type,
            "max_steps": db_simulation.max_steps
        }
        
        # 调用服务创建模拟
        try:
            sim_data = simulation_service.create_simulation(db_simulation.id, config)
        except Exception as service_error:
            logger.error(f"调用模拟服务失败: {str(service_error)}")
            db.delete(db_simulation)
            db.commit()
            raise service_error
        
        # 保存智能体记录
        try:
            # 创建猎手记录
            for hunter in sim_data["hunters"]:
                hunter_agent = Agent(
                    simulation_id=db_simulation.id,
                    agent_id=hunter["id"],
                    type="hunter",
                    start_position_x=hunter["position"][0],
                    start_position_y=hunter["position"][1],
                    velocity=hunter["velocity"],
                    vision_range=100.0,
                    communication_range=hunter["communication_range"]
                )
                db.add(hunter_agent)
            
            # 创建目标记录
            for target in sim_data["targets"]:
                target_agent = Agent(
                    simulation_id=db_simulation.id,
                    agent_id=target["id"],
                    type="target",
                    start_position_x=target["position"][0],
                    start_position_y=target["position"][1],
                    velocity=target["velocity"],
                    vision_range=60.0,
                    communication_range=0
                )
                db.add(target_agent)
            
            # 提交事务
            db.commit()
            
        except Exception as agent_error:
            logger.error(f"创建智能体记录失败: {str(agent_error)}")
            db.rollback()
            # 尝试清理服务中的模拟
            try:
                simulation_service.delete_simulation(db_simulation.id)
            except:
                pass
            raise agent_error
        
        # 记录成功并返回结果
        logger.info(f"模拟创建成功，ID: {db_simulation.id}")
        result_dict = db_simulation.to_dict()
        result_dict.update(sim_data)
        return result_dict
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建模拟失败: {str(e)}")
        # 添加详细的堆栈跟踪以便更好地诊断
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建模拟失败: {str(e)}")

# 获取单个模拟详情
@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
def get_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """获取单个模拟详情"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        # 获取模拟数据
        sim_data = simulation_service.get_simulation(simulation_id)
        return {**simulation.to_dict(), **sim_data}
    except ValueError:
        # 如果服务中没有该模拟，创建一个
        config = {
            "environment_size": simulation.environment_size,
            "num_hunters": simulation.num_hunters,
            "num_targets": simulation.num_targets,
            "algorithm_type": simulation.algorithm_type,
            "max_steps": simulation.max_steps
        }
        sim_data = simulation_service.create_simulation(simulation_id, config)
        return {**simulation.to_dict(), **sim_data}

# 启动模拟
@router.post("/simulations/{simulation_id}/start")
def start_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """启动模拟"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        # 设置开始时间
        simulation.start_time = datetime.utcnow()
        db.commit()
        
        # 启动模拟
        logger.info(f"启动模拟 ID: {simulation_id}")
        return simulation_service.start_simulation(simulation_id)
    except Exception as e:
        db.rollback()
        logger.error(f"启动模拟失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动模拟失败: {str(e)}")

# 停止模拟
@router.post("/simulations/{simulation_id}/stop")
def stop_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """停止模拟"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        logger.info(f"停止模拟 ID: {simulation_id}")
        result = simulation_service.stop_simulation(simulation_id)
        
        # 更新数据库状态
        if result["is_captured"] and not simulation.end_time:
            simulation.end_time = datetime.utcnow()
            simulation.is_captured = True
            simulation.capture_time = (simulation.end_time - simulation.start_time).total_seconds() if simulation.start_time else None
        
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"停止模拟失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止模拟失败: {str(e)}")

# 重置模拟
@router.post("/simulations/{simulation_id}/reset")
def reset_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """重置模拟"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        # 重置模拟状态
        simulation.step_count = 0
        simulation.is_captured = False
        simulation.start_time = None
        simulation.end_time = None
        simulation.capture_time = None
        db.commit()
        
        # 重置模拟服务
        logger.info(f"重置模拟 ID: {simulation_id}")
        return simulation_service.reset_simulation(simulation_id)
    except Exception as e:
        db.rollback()
        logger.error(f"重置模拟失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置模拟失败: {str(e)}")

# 删除模拟
@router.delete("/simulations/{simulation_id}")
def delete_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """删除模拟"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        # 从数据库删除模拟
        db.delete(simulation)
        db.commit()
        
        # 从服务中删除模拟
        logger.info(f"删除模拟 ID: {simulation_id}")
        simulation_service.delete_simulation(simulation_id)
        
        return {"message": "模拟已成功删除"}
    except Exception as e:
        db.rollback()
        logger.error(f"删除模拟失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除模拟失败: {str(e)}")

# WebSocket连接以获取实时模拟更新
@router.websocket("/ws/simulations/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: int, db: Session = Depends(get_db)):
    client_id = f"{id(websocket)}_{simulation_id}"
    
    try:
        # 1. 先接受连接
        await websocket.accept()
        logger.info(f"WebSocket客户端 {client_id} 已连接到模拟 {simulation_id}")
        
        # 2. 验证模拟存在性
        db_simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
        if not db_simulation:
            logger.warning(f"客户端 {client_id} 尝试连接不存在的模拟 {simulation_id}")
            await websocket.send_json({"error": "模拟不存在"})
            await websocket.close(code=1008, reason="Simulation not found")
            return
        
        # 3. 获取并发送初始数据
        try:
            try:
                # 尝试从模拟服务获取数据
                initial_data = simulation_service.get_simulation(simulation_id)
            except ValueError:
                # 如果不存在则创建新模拟
                logger.info(f"模拟 {simulation_id} 在服务中不存在，尝试创建")
                config = {
                    "environment_size": db_simulation.environment_size,
                    "num_hunters": db_simulation.num_hunters,
                    "num_targets": db_simulation.num_targets,
                    "algorithm_type": db_simulation.algorithm_type,
                    "max_steps": db_simulation.max_steps
                }
                initial_data = simulation_service.create_simulation(simulation_id, config)
            
            # 发送初始数据
            await websocket.send_json(initial_data)
            logger.info(f"已发送模拟 {simulation_id} 的初始状态给客户端 {client_id}")
        except Exception as e:
            logger.error(f"准备初始数据失败: {str(e)}")
            await websocket.send_json({"error": f"获取模拟状态失败: {str(e)}"})
            await websocket.close(code=1011)
            return
        
        # 4. 主循环处理逻辑
        position_records_buffer = []
        last_db_commit_time = datetime.utcnow()
        batch_size = 50
        update_frequency = 0.1  # 更新频率(秒)
        
        while True:
            try:
                # 获取模拟状态
                sim_data = simulation_service.get_simulation(simulation_id)
                
                if sim_data["is_running"]:
                    # 前进一步
                    # 添加详细错误捕获
                    try:
                        # 前进一步
                        sim_data = await simulation_service.step_simulation(simulation_id)
                    except Exception as step_error:
                        logger.error(f"步进模拟时出错: {str(step_error)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # 发送错误信息到前端
                        await websocket.send_json({
                            "error": f"模拟步进失败: {str(step_error)}",
                            "id": simulation_id,
                            "is_running": False
                        })
                        # 停止模拟，避免继续尝试
                        try:
                            simulation_service.stop_simulation(simulation_id)
                        except:
                            pass
                        continue
                    
                    # 更新数据库状态 (每10步更新一次)
                    if sim_data["step_count"] % 10 == 0:
                        try:
                            # 创建快照
                            snapshot = SimulationSnapshot(
                                simulation_id=simulation_id,
                                step=sim_data["step_count"],
                                hunters_state=json.dumps([h for h in sim_data["hunters"]]),
                                targets_state=json.dumps([t for t in sim_data["targets"]])
                            )
                            db.add(snapshot)
                            
                            # 收集位置记录
                            for hunter in sim_data["hunters"]:
                                agent_id = db.query(Agent.id).filter(
                                    Agent.simulation_id == simulation_id,
                                    Agent.agent_id == hunter["id"],
                                    Agent.type == "hunter"
                                ).scalar()
                                
                                if agent_id:
                                    position_records_buffer.append({
                                        "agent_id": agent_id,
                                        "step": sim_data["step_count"],
                                        "position_x": hunter["position"][0],
                                        "position_y": hunter["position"][1]
                                    })
                            
                            for target in sim_data["targets"]:
                                agent_id = db.query(Agent.id).filter(
                                    Agent.simulation_id == simulation_id,
                                    Agent.agent_id == target["id"],
                                    Agent.type == "target"
                                ).scalar()
                                
                                if agent_id:
                                    position_records_buffer.append({
                                        "agent_id": agent_id,
                                        "step": sim_data["step_count"],
                                        "position_x": target["position"][0],
                                        "position_y": target["position"][1]
                                    })
                            
                            # 判断是否应该提交数据库操作
                            current_time = datetime.utcnow()
                            time_diff = (current_time - last_db_commit_time).total_seconds()
                            should_commit = (len(position_records_buffer) >= batch_size or 
                                            time_diff > 5.0 or 
                                            sim_data["is_captured"])
                            
                            if should_commit and position_records_buffer:
                                # 批量插入位置记录
                                db.execute(AgentPosition.__table__.insert(), position_records_buffer)
                                position_records_buffer = []
                                
                                # 更新模拟状态
                                db_simulation.step_count = sim_data["step_count"]
                                db_simulation.is_captured = sim_data["is_captured"]
                                
                                if sim_data["is_captured"] and not db_simulation.end_time:
                                    db_simulation.end_time = current_time
                                    db_simulation.capture_time = (db_simulation.end_time - db_simulation.start_time).total_seconds() if db_simulation.start_time else None
                                
                                db.commit()
                                last_db_commit_time = current_time
                                logger.debug(f"已提交数据到数据库，步数: {sim_data['step_count']}")
                        except Exception as db_error:
                            logger.error(f"数据库操作失败: {str(db_error)}")
                            db.rollback()
                
                # 发送状态更新
                await websocket.send_json(sim_data)
                
                # 接收可能的客户端消息（非阻塞方式）
                try:
                    message_data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                    try:
                        message = json.loads(message_data)
                        # 处理心跳消息
                        if message.get('type') == 'heartbeat':
                            await websocket.send_json({"heartbeat": True, "timestamp": datetime.utcnow().isoformat()})
                    except json.JSONDecodeError:
                        logger.warning(f"收到无效的JSON消息: {message_data}")
                except asyncio.TimeoutError:
                    # 超时没关系，继续循环
                    pass
                except Exception as e:
                    if "connection closed" in str(e).lower() or "disconnected" in str(e).lower():
                        logger.info(f"客户端 {client_id} 已断开连接")
                        break
                    else:
                        logger.warning(f"接收客户端消息时出错: {str(e)}")
                
                # 如果模拟未运行，数据应该有未提交的，确保提交
                if not sim_data["is_running"] and position_records_buffer:
                    try:
                        db.execute(AgentPosition.__table__.insert(), position_records_buffer)
                        position_records_buffer = []
                        db.commit()
                        logger.debug("已提交未运行状态的位置记录数据")
                    except Exception as e:
                        logger.error(f"提交位置记录数据失败: {str(e)}")
                        db.rollback()
                
                # 控制更新频率
                await asyncio.sleep(update_frequency)
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"WebSocket连接已关闭: {client_id}, 原因: {str(e)}")
                break
            except ValueError as e:
                logger.error(f"模拟 {simulation_id} 不存在或数据无效: {str(e)}")
                await websocket.send_json({"error": f"模拟数据错误: {str(e)}"})
                break
            except Exception as e:
                logger.error(f"处理模拟 {simulation_id} 时出错: {str(e)}")
                try:
                    await websocket.send_json({"error": f"处理错误: {str(e)}"})
                except Exception:
                    pass
                break
        
        # 确保有未提交的数据被保存
        if position_records_buffer:
            try:
                db.execute(AgentPosition.__table__.insert(), position_records_buffer)
                db.commit()
                logger.debug(f"已提交剩余的位置记录数据, 记录数: {len(position_records_buffer)}")
            except Exception as e:
                logger.error(f"提交剩余数据失败: {str(e)}")
                db.rollback()
        if sim_data["is_captured"] and not db_simulation.is_captured:
            db_simulation.is_captured = True
            db_simulation.end_time = datetime.utcnow()
            db_simulation.capture_time = (db_simulation.end_time - db_simulation.start_time).total_seconds() if db_simulation.start_time else None
            
            # 确保立即提交更改
            db.commit()
            logger.info(f"更新数据库：模拟 {simulation_id} 状态设置为已捕获")
    
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"WebSocket连接正常关闭: {client_id}")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"WebSocket连接异常关闭: {client_id}, 原因: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket连接发生意外错误: {str(e)}")
    finally:
        try:
            # 确保连接已关闭
            if websocket.client_state != websockets.enums.State.CLOSED:
                await websocket.close()
        except Exception:
            pass
        logger.info(f"WebSocket客户端 {client_id} 会话结束")

@router.post("/simulations/{simulation_id}/regenerate-obstacles")
def regenerate_obstacles(
    simulation_id: int, 
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """重新生成障碍物，确保不与智能体重叠"""
    logger.info(f"收到障碍物生成请求: simulation_id={simulation_id}, data={data}")
    
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        logger.error(f"模拟{simulation_id}不存在")
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        count = data.get("count", 3)
        logger.info(f"准备生成{count}个障碍物")
        
        # 获取模拟数据
        sim_data = simulation_service.get_simulation(simulation_id)
        
        # 生成新的障碍物
        env_size = simulation.environment_size
        obstacles = simulation_service.generate_obstacles(
            env_size=env_size,
            num_obstacles=count,
            hunters=sim_data.get("hunters", []),
            targets=sim_data.get("targets", [])
        )
        
        logger.info(f"成功生成{len(obstacles)}个障碍物")
        
        # 更新模拟中的障碍物
        updated_sim = simulation_service.update_simulation_obstacles(simulation_id, obstacles)
        
        # 更新数据库中的障碍物计数
        simulation.obstacle_count = len(obstacles)
        db.commit()
        
        return {"success": True, "obstacles": obstacles}
        
    except Exception as e:
        logger.error(f"重新生成障碍物失败: {str(e)}")
        logger.exception(e)  # 记录完整堆栈跟踪
        raise HTTPException(status_code=500, detail=f"重新生成障碍物失败: {str(e)}")

@router.put("/simulations/{simulation_id}/update-timestamp")
def update_simulation_timestamp(
    simulation_id: int,
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """更新模拟的时间戳"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    try:
        if "created_at" in data and data["created_at"]:
            try:
                # 尝试解析ISO格式的时间字符串
                created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
                simulation.created_at = created_at
            except ValueError:
                # 如果解析失败，使用当前时间
                simulation.created_at = datetime.utcnow()
        
        # 确保更新时间始终设置
        simulation.updated_at = datetime.utcnow()
        
        db.commit()
        return {"message": "时间戳已更新"}
    except Exception as e:
        db.rollback()
        logger.error(f"更新时间戳失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新时间戳失败: {str(e)}")

@router.get("/simulations/{simulation_id}/final-snapshot")
def get_final_snapshot(simulation_id: int, db: Session = Depends(get_db)):
    """获取模拟的最终状态快照"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="模拟不存在")
    
    # 获取最后一个快照
    last_snapshot = db.query(SimulationSnapshot).filter(
        SimulationSnapshot.simulation_id == simulation_id
    ).order_by(SimulationSnapshot.step.desc()).first()
    
    if not last_snapshot:
        return {
            "message": "未找到快照数据",
            "hunters": [],
            "targets": [],
            "step": simulation.step_count,
            "is_captured": simulation.is_captured,
            "capture_time": simulation.capture_time,
            "creation_time": simulation.created_at.isoformat() if simulation.created_at else None
        }
    
    # 解析JSON数据
    try:
        hunters = json.loads(last_snapshot.hunters_state)
    except:
        hunters = []
        
    try:
        targets = json.loads(last_snapshot.targets_state)
    except:
        targets = []
    
    return {
        "hunters": hunters,
        "targets": targets,
        "step": last_snapshot.step,
        "timestamp": last_snapshot.timestamp.isoformat() if last_snapshot.timestamp else None,
        "is_captured": simulation.is_captured,
        "capture_time": simulation.capture_time,
        "captured_targets_count": simulation.captured_targets_count,
        "creation_time": simulation.created_at.isoformat() if simulation.created_at else None
    }