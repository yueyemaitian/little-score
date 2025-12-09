# 局域网访问配置指南

本指南说明如何配置项目以支持在局域网内的手机上访问本地服务。

## 一、获取本机局域网 IP 地址

### macOS/Linux
```bash
# 方法1：查看所有网络接口
ifconfig | grep "inet " | grep -v 127.0.0.1

# 方法2：查看主要网络接口（通常是以太网或 Wi-Fi）
ipconfig getifaddr en0  # macOS Wi-Fi
ip addr show | grep "inet " | grep -v 127.0.0.1  # Linux

# 方法3：使用 hostname
hostname -I  # Linux
```

### Windows
```cmd
# 打开命令提示符（CMD）
ipconfig

# 查找 "IPv4 地址"，通常是 192.168.x.x 或 10.x.x.x
```

### 示例输出
```
inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```
你的局域网 IP 就是 `192.168.1.100`

## 二、配置开发环境

### 方式一：使用 Docker Compose（推荐）

1. **创建或修改 `.env` 文件**

```bash
# 获取本机局域网 IP（替换为你的实际 IP）
LOCAL_IP=192.168.1.100  # 替换为你的局域网 IP

# 后端 CORS 配置（允许局域网访问）
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://${LOCAL_IP}:5173,http://${LOCAL_IP}:80

# 前端 API 地址（手机访问时使用局域网 IP）
VITE_API_BASE_URL=http://${LOCAL_IP}:8000/api/v1
```

2. **修改 `docker-compose.dev.yml`**

```yaml
backend:
  environment:
    BACKEND_CORS_ORIGINS: ${BACKEND_CORS_ORIGINS:-http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1}

frontend:
  environment:
    VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://localhost:8000/api/v1}
```

3. **启动服务**

```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. **在手机上访问**

- 前端：`http://你的局域网IP:5173` 或 `http://你的局域网IP:80`（通过 Nginx）
- API：`http://你的局域网IP:8000/api/v1`

### 方式二：直接运行（不使用 Docker）

1. **后端配置**

创建 `.env` 文件：
```env
SQLALCHEMY_DATABASE_URI=mysql+aiomysql://user:password@localhost:3306/little_score
SECRET_KEY=your-secret-key
BACKEND_CORS_ORIGINS=http://localhost:5173,http://192.168.1.100:5173,http://192.168.1.100:80
```

启动后端：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. **前端配置**

创建 `frontend/.env.local` 文件：
```env
VITE_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

启动前端：
```bash
cd frontend
npm run dev
# Vite 会自动监听 0.0.0.0:5173
```

3. **在手机上访问**

- 前端：`http://192.168.1.100:5173`
- API：`http://192.168.1.100:8000/api/v1`

## 三、防火墙配置

### macOS
```bash
# 允许端口 5173（前端）
sudo pfctl -f /etc/pf.conf

# 或者通过系统设置：
# 系统设置 > 网络 > 防火墙 > 选项 > 允许传入连接
```

### Linux (Ubuntu/Debian)
```bash
# 允许端口 5173 和 8000
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp  # 如果使用 Nginx
```

### Windows
1. 打开"Windows Defender 防火墙"
2. 点击"高级设置"
3. 新建入站规则
4. 选择"端口"，允许 TCP 端口 5173、8000、80

## 四、快速配置脚本

创建 `setup-local-network.sh`：

```bash
#!/bin/bash

# 获取局域网 IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' || ip route get 1 | awk '{print $7}' | head -1)

if [ -z "$LOCAL_IP" ]; then
    echo "无法自动获取局域网 IP，请手动设置"
    exit 1
fi

echo "检测到局域网 IP: $LOCAL_IP"
echo ""

# 更新 .env 文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cat > .env << EOF
LOCAL_IP=$LOCAL_IP
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80
VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1
EOF
else
    echo "更新 .env 文件..."
    # 更新或添加 LOCAL_IP
    if grep -q "^LOCAL_IP=" .env; then
        sed -i.bak "s|^LOCAL_IP=.*|LOCAL_IP=$LOCAL_IP|" .env
    else
        echo "LOCAL_IP=$LOCAL_IP" >> .env
    fi
    
    # 更新 BACKEND_CORS_ORIGINS
    if grep -q "^BACKEND_CORS_ORIGINS=" .env; then
        sed -i.bak "s|^BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80|" .env
    else
        echo "BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80" >> .env
    fi
    
    # 更新 VITE_API_BASE_URL
    if grep -q "^VITE_API_BASE_URL=" .env; then
        sed -i.bak "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1|" .env
    else
        echo "VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1" >> .env
    fi
fi

echo ""
echo "配置完成！"
echo ""
echo "访问地址："
echo "  前端: http://$LOCAL_IP:5173"
echo "  前端(通过Nginx): http://$LOCAL_IP:80"
echo "  API: http://$LOCAL_IP:8000/api/v1"
echo ""
echo "请在手机上使用上述地址访问"
```

使用：
```bash
chmod +x setup-local-network.sh
./setup-local-network.sh
```

## 五、验证配置

1. **检查服务是否监听在 0.0.0.0**

```bash
# macOS/Linux
netstat -an | grep LISTEN | grep -E '5173|8000|80'

# 应该看到类似：
# tcp4  0  0  *.5173  *.*  LISTEN
# tcp4  0  0  *.8000  *.*  LISTEN
```

2. **在手机上测试**

- 确保手机和电脑在同一 Wi-Fi 网络
- 在手机浏览器访问：`http://你的局域网IP:5173`
- 如果无法访问，检查防火墙设置

## 六、常见问题

### Q: 手机无法访问
1. 检查手机和电脑是否在同一 Wi-Fi 网络
2. 检查防火墙是否允许端口访问
3. 检查 IP 地址是否正确
4. 尝试 ping：`ping 你的局域网IP`

### Q: CORS 错误
确保 `BACKEND_CORS_ORIGINS` 包含手机的访问地址（包括端口号）

### Q: API 请求失败
确保 `VITE_API_BASE_URL` 设置为局域网 IP，而不是 `localhost`

### Q: IP 地址变化
如果 IP 地址经常变化，可以：
1. 在路由器中设置静态 IP
2. 使用动态 DNS 服务
3. 每次 IP 变化后重新运行配置脚本

## 七、使用 Nginx 代理（推荐）

如果使用 Nginx，手机访问 `http://你的局域网IP:80` 即可，Nginx 会自动代理到前端和后端。

### Nginx 配置说明

`nginx/conf.d/default.conf` 已配置为：
- `listen 80;` - 监听所有网络接口（0.0.0.0:80）
- `server_name _;` - 匹配所有域名和 IP，支持 localhost 和局域网 IP 访问

**无需额外修改**，Nginx 配置已支持局域网访问。

### 确保配置正确

1. **后端 CORS 配置**：确保 `.env` 中的 `BACKEND_CORS_ORIGINS` 包含 `http://你的局域网IP:80`
2. **前端 API 地址**：如果通过 Nginx 访问，`VITE_API_BASE_URL` 可以设置为 `http://你的局域网IP:80/api/v1`（使用相对路径 `/api/v1` 也可以）

### 访问方式

- **通过 Nginx（推荐）**：`http://你的局域网IP:80`
  - 前端和后端都通过 Nginx 代理，统一入口
  
- **直接访问前端**：`http://你的局域网IP:5173`
  - 需要确保 `VITE_API_BASE_URL` 指向正确的后端地址

