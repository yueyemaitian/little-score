# 阿里云 ECS 部署指南

## 一、ECS 服务器准备

### 1.1 推荐配置

| 配置项 | 最低配置 | 推荐配置 |
|--------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 系统盘 | 40GB SSD | 80GB SSD |
| 数据盘 | 50GB | 100GB+ |
| 操作系统 | Ubuntu 22.04 / CentOS 8 | Ubuntu 22.04 LTS |
| 带宽 | 1Mbps | 5Mbps+ |

### 1.2 安全组配置

在阿里云控制台配置安全组，开放以下端口：

| 端口 | 协议 | 说明 |
|------|------|------|
| 22 | TCP | SSH 远程连接 |
| 80 | TCP | HTTP 访问 |
| 443 | TCP | HTTPS 访问 |
| 8000 | TCP | 后端 API（可选，生产环境建议关闭） |

## 二、服务器环境配置

### 2.1 连接到 ECS

```bash
ssh root@<你的ECS公网IP>
```

### 2.2 更新系统

```bash
# Ubuntu
apt update && apt upgrade -y

# CentOS
yum update -y
```

### 2.3 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
```

### 2.4 安装 Docker Compose

```bash
# 安装最新版 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 2.5 创建应用目录

```bash
mkdir -p /opt/little-score
cd /opt/little-score
```

## 三、部署应用

### 3.1 方式一：Git 克隆（推荐）

```bash
# 安装 Git
apt install git -y  # Ubuntu
# yum install git -y  # CentOS

# 克隆代码
git clone <你的仓库地址> /opt/little-score
cd /opt/little-score
```

### 3.2 方式二：手动上传

从本地上传代码到服务器：

```bash
# 在本地执行
scp -r /Users/fanhua/develop/pyspace/little-score root@<ECS公网IP>:/opt/
```

### 3.3 配置环境变量

```bash
cd /opt/little-score

# 创建生产环境配置文件
cat > .env << 'EOF'
# 数据库配置
MYSQL_ROOT_PASSWORD=<设置一个强密码>
MYSQL_DATABASE=little_score
MYSQL_USER=app_user
MYSQL_PASSWORD=<设置一个强密码>

# 应用配置
SECRET_KEY=<生成一个随机密钥>
BACKEND_CORS_ORIGINS=https://你的域名,http://你的域名

# 数据目录
MYSQL_DATA_DIR=/opt/little-score/data/mysql
LOG_DIR=/opt/little-score/logs
EOF
```

**生成随机密钥：**

```bash
# 生成 SECRET_KEY
openssl rand -hex 32
```

### 3.4 创建数据目录

```bash
mkdir -p /opt/little-score/data/mysql
mkdir -p /opt/little-score/logs/{backend,frontend,nginx,mysql}
chmod -R 755 /opt/little-score/data
chmod -R 755 /opt/little-score/logs
```

### 3.5 配置 Nginx（域名和 SSL）

#### 修改 Nginx 配置

编辑 `nginx/conf.d/default.conf`：

```bash
cat > nginx/conf.d/default.conf << 'EOF'
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name 你的域名;

    # 健康检查端点（不重定向）
    location /health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # 其他请求重定向到 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 主服务
server {
    listen 443 ssl http2;
    server_name 你的域名;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    client_max_body_size 10M;

    # 健康检查端点
    location /health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # API 路由 - 代理到后端
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端路由 - 代理到前端服务
    location / {
        proxy_pass http://frontend:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

#### 配置 SSL 证书

**方式一：阿里云免费证书**

1. 登录阿里云控制台 -> SSL 证书服务
2. 申请免费证书（每年 20 个免费 DV 证书）
3. 下载 Nginx 格式证书
4. 上传到服务器：

```bash
# 将证书文件放到 ssl 目录
mkdir -p /opt/little-score/nginx/ssl
# 上传 fullchain.pem 和 privkey.pem 到此目录
```

**方式二：Let's Encrypt 免费证书**

```bash
# 安装 certbot
apt install certbot -y

# 获取证书（先停止 nginx）
docker-compose -f docker-compose.prod.yml stop nginx
certbot certonly --standalone -d 你的域名

# 复制证书
cp /etc/letsencrypt/live/你的域名/fullchain.pem /opt/little-score/nginx/ssl/
cp /etc/letsencrypt/live/你的域名/privkey.pem /opt/little-score/nginx/ssl/
```

### 3.6 启动服务

```bash
cd /opt/little-score

# 构建并启动所有服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 四、域名配置

### 4.1 阿里云域名解析

1. 登录阿里云控制台 -> 云解析 DNS
2. 添加 A 记录：
   - 记录类型：A
   - 主机记录：@ 或 www
   - 记录值：你的 ECS 公网 IP
   - TTL：10分钟

### 4.2 等待 DNS 生效

```bash
# 验证 DNS 解析
ping 你的域名
nslookup 你的域名
```

## 五、运维管理

### 5.1 常用命令

```bash
cd /opt/little-score

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 更新代码后重新部署
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5.2 数据库备份

```bash
# 创建备份脚本
cat > /opt/little-score/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/little-score/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec little-score-db-prod mysqldump -u root -p${MYSQL_ROOT_PASSWORD} little_score > $BACKUP_DIR/db_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

chmod +x /opt/little-score/backup.sh

# 添加定时任务（每天凌晨 3 点备份）
echo "0 3 * * * /opt/little-score/backup.sh" | crontab -
```

### 5.3 SSL 证书自动续期（Let's Encrypt）

```bash
# 创建续期脚本
cat > /opt/little-score/renew-ssl.sh << 'EOF'
#!/bin/bash
cd /opt/little-score

# 停止 nginx
docker-compose -f docker-compose.prod.yml stop nginx

# 续期证书
certbot renew

# 复制新证书
cp /etc/letsencrypt/live/你的域名/fullchain.pem /opt/little-score/nginx/ssl/
cp /etc/letsencrypt/live/你的域名/privkey.pem /opt/little-score/nginx/ssl/

# 启动 nginx
docker-compose -f docker-compose.prod.yml start nginx
EOF

chmod +x /opt/little-score/renew-ssl.sh

# 添加定时任务（每月 1 号凌晨 2 点续期）
echo "0 2 1 * * /opt/little-score/renew-ssl.sh" | crontab -
```

### 5.4 监控服务

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看日志大小
du -sh /opt/little-score/logs/*
```

## 六、故障排查

### 6.1 服务无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs db

# 检查端口占用
netstat -tlnp | grep -E '80|443|8000|3306'
```

### 6.2 数据库连接失败

```bash
# 检查数据库容器
docker exec -it little-score-db-prod mysql -u root -p

# 检查网络
docker network ls
docker network inspect little-score_app-network
```

### 6.3 Nginx 502 错误

```bash
# 检查后端服务是否正常
docker-compose -f docker-compose.prod.yml logs backend

# 检查容器网络连通性
docker exec little-score-nginx-prod ping backend
```

## 七、安全建议

1. **修改 SSH 端口**：将默认 22 端口改为其他端口
2. **禁用 root 登录**：创建普通用户，使用 sudo
3. **配置防火墙**：只开放必要端口
4. **定期更新**：及时更新系统和 Docker
5. **备份数据**：定期备份数据库和配置文件
6. **监控告警**：配置阿里云云监控

```bash
# 修改 SSH 端口示例
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart sshd
```

## 八、快速部署脚本

一键部署脚本（在 ECS 上执行）：

```bash
#!/bin/bash
set -e

# 变量设置
APP_DIR="/opt/little-score"
REPO_URL="<你的 Git 仓库地址>"

echo "=== 开始部署 Little Score ==="

# 1. 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

# 2. 安装 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. 克隆代码
if [ ! -d "$APP_DIR" ]; then
    git clone $REPO_URL $APP_DIR
fi

cd $APP_DIR

# 4. 创建目录
mkdir -p data/mysql logs/{backend,frontend,nginx,mysql} nginx/ssl

# 5. 创建环境配置（如果不存在）
if [ ! -f ".env" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    cat > .env << EOF
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)
MYSQL_DATABASE=little_score
MYSQL_USER=app_user
MYSQL_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$SECRET_KEY
BACKEND_CORS_ORIGINS=http://$(curl -s ifconfig.me)
MYSQL_DATA_DIR=$APP_DIR/data/mysql
LOG_DIR=$APP_DIR/logs
EOF
    echo "已创建 .env 文件，请根据需要修改配置"
fi

# 6. 启动服务
docker-compose -f docker-compose.prod.yml up -d --build

echo "=== 部署完成 ==="
echo "请访问: http://$(curl -s ifconfig.me)"
docker-compose -f docker-compose.prod.yml ps
```

保存为 `deploy.sh` 并执行：

```bash
chmod +x deploy.sh
./deploy.sh
```

