"""
健康检查端点
用于 Docker 容器健康检查和负载均衡器探测
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    基础健康检查
    返回服务运行状态
    """
    return {"status": "healthy", "service": "little-score-backend"}


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """
    数据库健康检查
    检查数据库连接是否正常
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    就绪检查
    检查服务是否准备好接收请求
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}

