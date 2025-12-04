#!/bin/bash
# 启动后端服务并保存日志

# 创建日志目录
mkdir -p logs

# 启动服务并重定向日志
python3 -m uvicorn app.main:app --reload \
    >> logs/backend-$(date +%Y%m%d).log 2>&1

