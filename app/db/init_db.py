"""初始化数据库，创建默认的系统设置"""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_maker
from app.models.system import SystemSettings


async def init_db() -> None:
    """初始化数据库，确保系统设置存在"""
    async with async_session_maker() as session:
        # 检查是否已有系统设置
        result = await session.execute(select(SystemSettings).limit(1))
        settings = result.scalar_one_or_none()

        if settings is None:
            # 创建默认系统设置（允许注册）
            now = datetime.now(timezone.utc)
            settings = SystemSettings(
                allow_registration=True,
                created_at=now,
                updated_at=now,
            )
            session.add(settings)
            await session.commit()
            print("✓ 系统设置已初始化（默认允许注册）")
        else:
            print("✓ 系统设置已存在")


if __name__ == "__main__":
    asyncio.run(init_db())

