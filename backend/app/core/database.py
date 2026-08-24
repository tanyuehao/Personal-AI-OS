"""
Personal AI OS - Database Configuration
数据库配置模块
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# 创建异步引擎 - 支持 PostgreSQL 和 SQLite
is_sqlite = "sqlite" in settings.DATABASE_URL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    **({} if is_sqlite else {"pool_size": 20, "max_overflow": 10})
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """模型基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    """
    async with async_session_factory() as session:
        try:
            yield session
            # 兼容 endpoint 内已 commit 的情况
            if session.is_active:
                await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库表（幂等）"""
    async with engine.begin() as conn:
        def _create_tables(sync_conn):
            # 使用 checkfirst=True 确保幂等
            for table in Base.metadata.sorted_tables:
                table.create(sync_conn, checkfirst=True)
        await conn.run_sync(_create_tables)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
