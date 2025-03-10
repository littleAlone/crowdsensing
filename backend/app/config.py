from pydantic_settings import BaseSettings
import os
from typing import Any, Dict, List, Optional, Union

class Settings(BaseSettings):
    # 应用设置
    APP_NAME: str = "Multi-Agent Pursuit System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API设置
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/v1"
    
    # CORS设置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080", "http://192.168.1.100:8080"]
    
    # 数据库设置
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"  # 是否输出SQL语句
    
    # 模拟设置
    DEFAULT_ENV_SIZE: int = 500
    DEFAULT_NUM_HUNTERS: int = 5
    DEFAULT_NUM_TARGETS: int = 1
    DEFAULT_ALGORITHM: str = "APF"
    DEFAULT_MAX_STEPS: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量

# 创建设置实例
settings = Settings()