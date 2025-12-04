from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

    # CORS for web / WeChat browser
    # 处理 CORS 配置，同时支持带斜杠和不带斜杠的 Origin
    cors_origins = settings.BACKEND_CORS_ORIGINS
    if isinstance(cors_origins, str):
        cors_origins = [cors_origins]
    elif not cors_origins:
        cors_origins = ["*"]  # 开发环境允许所有来源
    else:
        # 将 AnyUrl 对象转换为字符串，并同时支持带斜杠和不带斜杠的版本
        normalized_origins = set()  # 使用 set 避免重复
        for origin in cors_origins:
            origin_str = str(origin)
            # 添加原始版本
            normalized_origins.add(origin_str)
            # 添加规范化版本（移除末尾斜杠）
            normalized_origins.add(origin_str.rstrip('/'))
            # 如果原始版本没有斜杠，添加带斜杠的版本
            if origin_str and not origin_str.endswith('/'):
                normalized_origins.add(origin_str + '/')
        cors_origins = list(normalized_origins)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()




