from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db_config import DB_FILE
import os
import logging

logger = logging.getLogger(__name__)

# 确保数据目录存在
data_dir = os.path.dirname(DB_FILE)
os.makedirs(data_dir, exist_ok=True)

# 导出db_file变量以保持与main.py的兼容性
db_file = DB_FILE

logger.info(f"使用数据库文件: {db_file}")

# 创建SQLite数据库URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.DB_ECHO,  # 是否输出SQL语句
    connect_args={"check_same_thread": False}  # 允许多线程访问SQLite数据库
)

# 创建会话本地类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# 获取数据库会话的依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(force_recreate=False):
    """初始化数据库表结构"""
    from app.models.db_models import Simulation, Agent, AgentPosition, SimulationSnapshot
    
    try:
        logger.info("开始初始化数据库...")
        
        # 检查表是否存在
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"现有表: {existing_tables}")
        
        # 如果需要重建表
        if force_recreate and existing_tables:
            logger.warning("正在删除所有现有表...")
            Base.metadata.drop_all(bind=engine)
            existing_tables = []
        
        # 定义需要的表
        required_tables = ['simulations', 'agents', 'agent_positions', 'simulation_snapshots']
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.info(f"创建缺失的表: {missing_tables}")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表创建完成")
        else:
            logger.info("所有必要的表已存在")
        
        # 验证表是否创建成功
        inspector = inspect(engine)
        updated_tables = inspector.get_table_names()
        still_missing = [table for table in required_tables if table not in updated_tables]
        
        if still_missing:
            logger.error(f"表创建失败，缺少以下表: {still_missing}")
            return False
            
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"初始化数据库时出错: {str(e)}")
        return False