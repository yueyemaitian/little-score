# 日志管理指南

## 后端日志位置

### 1. 直接运行 uvicorn（当前方式）

**日志位置：**
- 日志输出到标准输出/标准错误
- 后台运行时日志不可见

**查看日志的方法：**

#### 方法1：查看实时日志（推荐）
```bash
# 停止当前后台进程
pkill -f "uvicorn app.main:app"

# 前台运行查看日志
python3 -m uvicorn app.main:app --reload
```

#### 方法2：保存日志到文件
```bash
# 停止当前后台进程
pkill -f "uvicorn app.main:app"

# 使用脚本启动（自动保存日志）
./start-backend.sh

# 或手动重定向日志
python3 -m uvicorn app.main:app --reload >> logs/backend.log 2>&1 &
```

#### 方法3：使用 tail 查看日志文件
```bash
# 实时查看日志
tail -f logs/backend-$(date +%Y%m%d).log

# 或查看最新日志
tail -n 100 logs/backend-*.log
```

### 2. 使用 PM2 运行

**日志位置：**
- 错误日志：`./logs/backend-error.log`
- 输出日志：`./logs/backend-out.log`

**查看日志：**
```bash
# 启动服务
pm2 start ecosystem.config.js

# 查看实时日志
pm2 logs little-score-backend

# 查看错误日志
pm2 logs little-score-backend --err

# 查看输出日志
pm2 logs little-score-backend --out

# 查看最后100行
pm2 logs little-score-backend --lines 100
```

### 3. 使用 Docker 运行

**查看日志：**
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看最后100行
docker-compose logs --tail=100 backend
```

## 日志级别

Uvicorn 默认日志级别：
- INFO: 请求日志、启动信息
- WARNING: 警告信息
- ERROR: 错误信息
- DEBUG: 调试信息（需要设置）

## 配置日志级别

### 方法1：命令行参数
```bash
# 设置日志级别
python3 -m uvicorn app.main:app --reload --log-level debug
```

### 方法2：环境变量
```bash
export UVICORN_LOG_LEVEL=debug
python3 -m uvicorn app.main:app --reload
```

### 方法3：代码配置
在 `app/main.py` 中配置：
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 日志轮转

### 使用 logrotate（Linux）
创建 `/etc/logrotate.d/little-score`：
```
/path/to/little-score/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

### 使用脚本
```bash
# 清理7天前的日志
find logs/ -name "*.log" -mtime +7 -delete
```

## 快速命令

```bash
# 查看当前运行的后端进程
ps aux | grep uvicorn

# 停止后端服务
pkill -f "uvicorn app.main:app"

# 查看最新日志（如果使用脚本启动）
tail -f logs/backend-$(date +%Y%m%d).log

# 搜索错误日志
grep -i error logs/backend-*.log

# 搜索特定API请求
grep "POST /api/v1" logs/backend-*.log
```

