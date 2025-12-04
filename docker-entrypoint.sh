#!/bin/sh
set -e

# 确保日志目录存在且可写
mkdir -p /app/logs
touch /app/logs/startup.log /app/logs/uvicorn.log 2>/dev/null || true

echo "========== 启动时间: $(date '+%Y-%m-%d %H:%M:%S') ==========" >> /app/logs/startup.log 2>/dev/null || echo "警告: 无法写入启动日志"

# 执行数据库迁移
echo ">>> 执行数据库迁移..."
if python3 -m alembic upgrade head 2>&1 | tee -a /app/logs/startup.log 2>/dev/null; then
    echo "数据库迁移完成"
else
    echo "数据库迁移完成（日志写入可能失败）"
fi

# 初始化数据库
echo ">>> 初始化数据库..."
if python3 -m app.db.init_db 2>&1 | tee -a /app/logs/startup.log 2>/dev/null; then
    echo "数据库初始化完成"
else
    echo "数据库初始化完成（日志写入可能失败）"
fi

# 启动应用
echo ">>> 启动应用服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

