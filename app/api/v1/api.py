from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, dashboard, enums, health, projects, scores, students, tasks, users

api_router = APIRouter()

# 健康检查（无需认证）
api_router.include_router(health.router, tags=["健康检查"])

# 业务接口
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(students.router, prefix="/students", tags=["学生管理"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(scores.router, prefix="/scores", tags=["积分管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["首页"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
api_router.include_router(enums.router, prefix="/enums", tags=["枚举值"])




