import json
import os
from pathlib import Path
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Little Score API"
    API_V1_STR: str = "/api/v1"

    # MySQL DSN，例如：mysql+aiomysql://user:password@localhost:3306/little_score
    SQLALCHEMY_DATABASE_URI: str

    # JWT 设置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    ALGORITHM: str = "HS256"

    # 允许的前端跨域地址（支持 JSON 数组字符串或逗号分隔的字符串）
    BACKEND_CORS_ORIGINS: Union[List[AnyUrl], str] = []

    # AI 大模型配置（支持 DeepSeek、Qwen 等 OpenAI 兼容 API）
    AI_API_KEY: Optional[str] = None
    AI_API_BASE_URL: str = "https://api.deepseek.com"  # 默认使用 DeepSeek
    AI_MODEL: str = "deepseek-chat"  # 默认模型

    # 微信登录配置
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None

    # 钉钉登录配置
    DINGTALK_APP_KEY: Optional[str] = None
    DINGTALK_APP_SECRET: Optional[str] = None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # 尝试解析 JSON 数组
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # 如果不是 JSON，尝试按逗号分割
            if v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            return []
        return v

    model_config = SettingsConfigDict(
        # 使用绝对路径，确保能找到 .env 文件
        # 从当前文件位置向上查找项目根目录的 .env 文件
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        # 同时支持从环境变量读取（优先级更高）
        env_ignore_empty=True,
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[arg-type]
    
    # 开发环境：打印配置信息（不包含敏感信息）
    if os.getenv("ENVIRONMENT", "").lower() != "production":
        print(f"✓ 配置已加载:")
        print(f"  - WECHAT_APP_ID: {'已配置' if settings.WECHAT_APP_ID else '未配置'}")
        print(f"  - WECHAT_APP_SECRET: {'已配置' if settings.WECHAT_APP_SECRET else '未配置'}")
        print(f"  - DINGTALK_APP_KEY: {'已配置' if settings.DINGTALK_APP_KEY else '未配置'}")
        print(f"  - DINGTALK_APP_SECRET: {'已配置' if settings.DINGTALK_APP_SECRET else '未配置'}")
    
    return settings


