# create_db_standalone.py
import os
import sqlite3
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
logger.info(f"项目根目录: {PROJECT_ROOT}")

# 定义数据库路径（在项目根目录的data文件夹下）
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, 'simulation.db')
logger.info(f"数据库文件路径: {DB_FILE}")

# 创建数据库目录及删除现有数据库
def prepare_database(force_recreate=False):
    if force_recreate and os.path.exists(DB_FILE):
        logger.info(f"删除现有数据库文件: {DB_FILE}")
        os.remove(DB_FILE)
    
    logger.info(f"确保数据目录存在: {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 创建一个空的数据库文件
    if not os.path.exists(DB_FILE):
        logger.info("创建新的空SQLite数据库文件")
        conn = sqlite3.connect(DB_FILE)
        conn.close()

# 创建表的SQL语句
CREATE_TABLE_SQL = [
    """
    CREATE TABLE simulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        environment_size INTEGER DEFAULT 500,
        num_hunters INTEGER DEFAULT 5,
        num_targets INTEGER DEFAULT 1,
        algorithm_type VARCHAR(50) DEFAULT 'APF',
        max_steps INTEGER DEFAULT 1000,
        is_captured BOOLEAN DEFAULT 0,
        step_count INTEGER DEFAULT 0,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        capture_time FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        captured_targets_count INTEGER DEFAULT 0,
        escaped_targets_count INTEGER DEFAULT 0,
        total_targets_count INTEGER DEFAULT 0,
        obstacle_count INTEGER DEFAULT 0,
        escaped BOOLEAN DEFAULT 0,
        escape_time FLOAT
    )
    """,
    """
    CREATE TABLE agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulation_id INTEGER NOT NULL,
        agent_id INTEGER NOT NULL,
        type VARCHAR(20) NOT NULL,
        start_position_x FLOAT NOT NULL,
        start_position_y FLOAT NOT NULL,
        velocity FLOAT DEFAULT 1.0,
        vision_range FLOAT DEFAULT 100.0,
        communication_range FLOAT DEFAULT 150.0,
        FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE agent_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        step INTEGER NOT NULL,
        position_x FLOAT NOT NULL,
        position_y FLOAT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE simulation_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulation_id INTEGER NOT NULL,
        step INTEGER NOT NULL,
        hunters_state TEXT NOT NULL,
        targets_state TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_final BOOLEAN DEFAULT 0,
        captured_targets_count INTEGER DEFAULT 0,
        escaped_targets_count INTEGER DEFAULT 0,
        FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
    )
    """
]

# 创建数据库表
def create_tables():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 执行建表语句
        for sql in CREATE_TABLE_SQL:
            logger.info(f"执行SQL: {sql.strip().split('(')[0]}")
            cursor.execute(sql)
        
        # 提交事务
        conn.commit()
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        # 检查所需的表是否都已创建
        required_tables = ['simulations', 'agents', 'agent_positions', 'simulation_snapshots']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            logger.error(f"表创建失败，缺少以下表: {missing_tables}")
            return False
        else:
            logger.info(f"数据库表创建成功！已创建表: {table_names}")
            return True
        
    except Exception as e:
        logger.error(f"创建数据库表时出错: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 创建配置文件，保存数据库路径
def create_db_config():
    config_dir = os.path.join(PROJECT_ROOT, 'app')
    config_file = os.path.join(config_dir, 'db_config.py')
    
    with open(config_file, 'w') as f:
        f.write(f"""# 自动生成的数据库配置
import os

# 数据库文件路径
DB_FILE = r"{DB_FILE}"
""")
    
    logger.info(f"数据库配置文件已创建: {config_file}")

# 主函数
if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='初始化模拟系统数据库')
    parser.add_argument('--force', action='store_true', help='强制重新创建数据库（会删除现有数据）')
    args = parser.parse_args()
    
    # 准备数据库文件
    prepare_database(force_recreate=args.force)
    
    # 创建表
    if create_tables():
        # 创建配置文件，为应用提供数据库路径
        create_db_config()
        print("数据库初始化成功！")
        sys.exit(0)
    else:
        print("数据库初始化失败，请查看日志了解详情。")
        sys.exit(1)