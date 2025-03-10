import os
import json
import csv
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import pandas as pd

from app.models.db_models import Simulation, Agent, AgentPosition, SimulationSnapshot
from app.database import SessionLocal

logger = logging.getLogger(__name__)

class CleanupService:
    """数据清理服务，负责管理历史数据和导出功能"""
    
    def __init__(self, 
                 data_retention_days: int = 30, 
                 export_dir: str = None):
        """
        初始化清理服务
        
        Args:
            data_retention_days: 数据保留天数，默认30天
            export_dir: 数据导出目录，默认为项目根目录下的exports文件夹
        """
        self.data_retention_days = data_retention_days
        
        # 设置导出目录
        if export_dir is None:
            # 默认在项目根目录下创建exports文件夹
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_dir = os.path.join(base_dir, 'exports')
        
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        
        logger.info(f"Cleanup service initialized with data retention of {data_retention_days} days")
        logger.info(f"Export directory set to: {export_dir}")
    
    async def start_scheduled_cleanup(self, interval_hours: int = 24):
        """
        启动定期清理任务
        
        Args:
            interval_hours: 清理间隔小时数
        """
        logger.info(f"Starting scheduled cleanup every {interval_hours} hours")
        while True:
            try:
                # 执行清理
                await self.cleanup_old_simulations()
                # 等待下一次清理
                await asyncio.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error(f"Error in scheduled cleanup: {str(e)}")
                # 即使出错也等待一段时间再重试
                await asyncio.sleep(3600)
    
    async def cleanup_old_simulations(self):
        """清理过期的模拟数据"""
        try:
            logger.info("Starting cleanup of old simulations")
            # 计算截止日期
            cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
            
            # 获取数据库会话
            db = SessionLocal()
            try:
                # 检查表是否存在
                from sqlalchemy import inspect
                inspector = inspect(db.bind)
                if 'simulations' not in inspector.get_table_names():
                    logger.warning("Simulations table does not exist yet, skipping cleanup")
                    return
                    
                # 查找过期的模拟
                old_simulations = db.query(Simulation).filter(
                    Simulation.created_at < cutoff_date
                ).all()
                
                if not old_simulations:
                    logger.info("No old simulations found to clean up")
                    return
                
                logger.info(f"Found {len(old_simulations)} old simulations to clean up")
                
                # 导出并删除每个过期模拟
                for simulation in old_simulations:
                    try:
                        # 先导出数据
                        await self.export_simulation(db, simulation.id)
                        
                        # 删除相关数据（利用外键CASCADE删除）
                        db.delete(simulation)
                        logger.info(f"Deleted simulation {simulation.id}: {simulation.name}")
                    except Exception as e:
                        logger.error(f"Error processing simulation {simulation.id}: {str(e)}")
                        # 继续处理其他模拟
                
                # 提交事务
                db.commit()
                logger.info("Cleanup completed successfully")
                
                # 执行数据库优化（SQLite特定操作）
                db.execute("VACUUM")
                logger.info("Database optimized with VACUUM")
                
            except Exception as e:
                logger.error(f"Database error during cleanup: {str(e)}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Unexpected error in cleanup: {str(e)}")
    
    async def export_simulation(self, db: Session, simulation_id: int) -> str:
        """
        导出模拟数据到CSV和JSON文件
        
        Args:
            db: 数据库会话
            simulation_id: 模拟ID
            
        Returns:
            str: 导出目录路径
        """
        logger.info(f"Exporting simulation {simulation_id}")
        
        # 获取模拟数据
        simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
        if not simulation:
            logger.warning(f"Simulation {simulation_id} not found for export")
            return None
        
        # 创建导出子目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_subdir = os.path.join(self.export_dir, f"sim_{simulation_id}_{timestamp}")
        os.makedirs(export_subdir, exist_ok=True)
        
        # 导出模拟基本信息（JSON）
        sim_info = simulation.to_dict()
        with open(os.path.join(export_subdir, "simulation_info.json"), 'w', encoding='utf-8') as f:
            json.dump(sim_info, f, ensure_ascii=False, indent=2)
        
        # 导出智能体数据（CSV）
        agents = db.query(Agent).filter(Agent.simulation_id == simulation_id).all()
        if agents:
            agent_data = [agent.to_dict() for agent in agents]
            df_agents = pd.DataFrame(agent_data)
            df_agents.to_csv(os.path.join(export_subdir, "agents.csv"), index=False)
        
        # 导出位置历史（CSV，分批处理大数据）
        positions_query = db.query(AgentPosition).join(
            Agent, Agent.id == AgentPosition.agent_id
        ).filter(
            Agent.simulation_id == simulation_id
        )
        
        # 计算记录数量
        positions_count = positions_query.count()
        logger.info(f"Exporting {positions_count} position records for simulation {simulation_id}")
        
        if positions_count > 0:
            # 使用pandas分批处理和写入
            batch_size = 10000
            batches = (positions_count // batch_size) + (1 if positions_count % batch_size else 0)
            
            with open(os.path.join(export_subdir, "positions.csv"), 'w', newline='') as f:
                # 先写入CSV头
                writer = csv.writer(f)
                writer.writerow(["agent_id", "step", "position_x", "position_y", "timestamp"])
                
                # 分批处理数据
                for i in range(batches):
                    positions_batch = positions_query.order_by(
                        AgentPosition.agent_id, AgentPosition.step
                    ).offset(i * batch_size).limit(batch_size).all()
                    
                    for position in positions_batch:
                        writer.writerow([
                            position.agent_id,
                            position.step,
                            position.position_x,
                            position.position_y,
                            position.timestamp.isoformat() if position.timestamp else None
                        ])
        
        # 导出快照数据（JSON）
        snapshots = db.query(SimulationSnapshot).filter(
            SimulationSnapshot.simulation_id == simulation_id
        ).order_by(SimulationSnapshot.step).all()
        
        if snapshots:
            snapshots_data = [snapshot.to_dict() for snapshot in snapshots]
            with open(os.path.join(export_subdir, "snapshots.json"), 'w', encoding='utf-8') as f:
                json.dump(snapshots_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Export completed to {export_subdir}")
        return export_subdir
    
    async def export_all_simulations(self):
        """导出所有模拟数据"""
        logger.info("Starting export of all simulations")
        db = SessionLocal()
        try:
            simulations = db.query(Simulation).all()
            logger.info(f"Found {len(simulations)} simulations to export")
            
            for simulation in simulations:
                try:
                    await self.export_simulation(db, simulation.id)
                except Exception as e:
                    logger.error(f"Error exporting simulation {simulation.id}: {str(e)}")
            
            logger.info("Export of all simulations completed")
        except Exception as e:
            logger.error(f"Error in export_all_simulations: {str(e)}")
        finally:
            db.close()

# 创建一个方法用于在应用启动时初始化清理服务
def init_cleanup_service(app):
    """
    初始化清理服务并添加到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    cleanup_service = CleanupService()
    app.state.cleanup_service = cleanup_service
    
    @app.on_event("startup")
    async def start_cleanup_task():
        # 启动定期清理任务，在后台运行
        asyncio.create_task(cleanup_service.start_scheduled_cleanup())