from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.api.routes import router as api_router
from app.config import settings
from app.database import engine, Base, init_db, db_file
from app.services.cleanup_service import init_cleanup_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def get_application() -> FastAPI:
    """创建FastAPI应用"""
    # 创建FastAPI实例
    app = FastAPI(
        title=settings.APP_NAME,
        description="多智能体围捕系统API",
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
    )
    
    # 配置CORS，明确设置允许的源
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 明确指定允许的前端源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 应用启动事件
    @app.on_event("startup")
    async def startup_events():
        # 初始化数据库
        db_initialized = init_db()
        if not db_initialized:
            logger.warning("数据库初始化失败，尝试强制重建...")
            db_initialized = init_db(force_recreate=True)
            
        if not db_initialized:
            logger.error("数据库初始化仍然失败，应用可能无法正常工作")
        else:
            # 初始化清理服务
            init_cleanup_service(app)
    
    # 挂载API路由
    app.include_router(api_router, prefix=f"{settings.API_PREFIX}{settings.API_V1_STR}")
    
    return app

app = get_application()

@app.get("/")
async def root():
    """健康检查端点"""
    return {"status": "ok", "message": "Multi-Agent Pursuit System API is running"}

if __name__ == "__main__":
    # 用于本地开发的启动代码
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)