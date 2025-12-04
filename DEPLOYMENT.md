# 部署文档

## 部署方式

### 1. Docker Compose 部署（推荐）

#### 开发环境
```bash
# 创建 .env 文件
# cp .env.example .env
# 编辑 .env 文件，配置数据库和密钥

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止
docker-compose -f docker-compose.dev.yml down
```

#### 生产环境
```bash
# 创建生产环境 .env 文件
# cp .env.example .env.prod
# 编辑 .env.prod 文件，配置生产环境变量

# 启动生产环境
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止
docker-compose -f docker-compose.prod.yml down
```

### 2. PM2 部署（仅后端）

#### 安装 PM2
```bash
npm install -g pm2
```

#### 启动应用
```bash
# 启动后端
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs little-score-backend

# 停止
pm2 stop little-score-backend

# 重启
pm2 restart little-score-backend

# 保存 PM2 配置
pm2 save
pm2 startup
```

### 3. 传统部署

#### 后端部署
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 运行数据库迁移
python3 -m alembic upgrade head
python3 -m app.db.init_db

# 4. 启动服务
# 使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用 gunicorn（推荐生产环境）
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 前端部署
```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 API 地址

# 3. 构建
npm run build

# 4. 部署 dist 目录到 Nginx 或静态服务器
```

### 4. Nginx 配置

#### 开发环境
使用 `nginx/conf.d/default.conf` 配置，通过 Docker Compose 自动配置。

#### 生产环境
```nginx
# /etc/nginx/sites-available/little-score
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/little-score /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 环境变量

### 后端 (.env)
```env
SQLALCHEMY_DATABASE_URI=mysql+aiomysql://user:password@host:3306/database
SECRET_KEY=your-secret-key-here
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

### 前端 (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Docker Compose
```env
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=little_score
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password
SECRET_KEY=your-secret-key
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 数据库迁移

```bash
# 创建新迁移
python3 -m alembic revision --autogenerate -m "描述"

# 应用迁移
python3 -m alembic upgrade head

# 回退迁移
python3 -m alembic downgrade -1

# 查看当前版本
python3 -m alembic current

# 查看历史
python3 -m alembic history
```

## SSL/HTTPS 配置

1. 获取 SSL 证书（使用 Let's Encrypt）
```bash
sudo certbot certonly --standalone -d your-domain.com
```

2. 更新 Nginx 配置，添加 SSL
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... 其他配置
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 监控和日志

### PM2 监控
```bash
# 查看监控面板
pm2 monit

# 查看详细信息
pm2 show little-score-backend
```

### Docker 日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
```

### 日志文件位置
- PM2: `./logs/backend-error.log`, `./logs/backend-out.log`
- Docker: `docker-compose logs`
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

## 备份和恢复

### 数据库备份
```bash
# 备份
docker-compose exec db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > backup.sql

# 恢复
docker-compose exec -T db mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < backup.sql
```

## 故障排查

1. **检查服务状态**
```bash
docker-compose ps
pm2 status
```

2. **查看日志**
```bash
docker-compose logs backend
pm2 logs
```

3. **检查数据库连接**
```bash
docker-compose exec db mysql -u root -p
```

4. **重启服务**
```bash
docker-compose restart
pm2 restart all
```

