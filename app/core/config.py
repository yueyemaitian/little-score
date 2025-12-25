import json
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
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


