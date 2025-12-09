#!/bin/bash

# 获取局域网 IP 地址
get_local_ip() {
    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
    # Linux
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1 2>/dev/null | awk '{print $7}' | head -1)
    fi
    
    # 如果还是获取不到，尝试其他方法
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    fi
    
    echo "$LOCAL_IP"
}

LOCAL_IP=$(get_local_ip)

if [ -z "$LOCAL_IP" ]; then
    echo "❌ 无法自动获取局域网 IP，请手动设置"
    echo ""
    echo "请手动编辑 .env 文件，设置："
    echo "  LOCAL_IP=你的局域网IP"
    echo "  BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://你的局域网IP:5173,http://你的局域网IP:80"
    echo "  VITE_API_BASE_URL=http://你的局域网IP:8000/api/v1"
    exit 1
fi

echo "✅ 检测到局域网 IP: $LOCAL_IP"
echo ""

# 更新或创建 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cat > .env << EOF
# 数据库配置
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=little_score
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password

# 应用配置
SECRET_KEY=dev-secret-key-change-in-production

# 局域网访问配置
LOCAL_IP=$LOCAL_IP
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80
VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1

# AI 语音助手配置（可选）
# AI_API_KEY=your-api-key
# AI_API_BASE_URL=https://api.deepseek.com
# AI_MODEL=deepseek-chat
EOF
    echo "✅ .env 文件已创建"
else
    echo "📝 更新 .env 文件..."
    
    # 备份原文件
    cp .env .env.bak 2>/dev/null || true
    
    # 更新或添加 LOCAL_IP
    if grep -q "^LOCAL_IP=" .env; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^LOCAL_IP=.*|LOCAL_IP=$LOCAL_IP|" .env
        else
            sed -i "s|^LOCAL_IP=.*|LOCAL_IP=$LOCAL_IP|" .env
        fi
    else
        echo "LOCAL_IP=$LOCAL_IP" >> .env
    fi
    
    # 更新 BACKEND_CORS_ORIGINS（添加局域网 IP）
    CORS_ORIGINS="http://localhost:5173,http://localhost,http://127.0.0.1:5173,http://127.0.0.1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80"
    if grep -q "^BACKEND_CORS_ORIGINS=" .env; then
        # 检查是否已包含局域网 IP
        if ! grep -q "$LOCAL_IP" .env | grep "BACKEND_CORS_ORIGINS"; then
            # 追加到现有配置
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^BACKEND_CORS_ORIGINS=\(.*\)|BACKEND_CORS_ORIGINS=\1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80|" .env
            else
                sed -i "s|^BACKEND_CORS_ORIGINS=\(.*\)|BACKEND_CORS_ORIGINS=\1,http://$LOCAL_IP:5173,http://$LOCAL_IP:80|" .env
            fi
        fi
    else
        echo "BACKEND_CORS_ORIGINS=$CORS_ORIGINS" >> .env
    fi
    
    # 更新 VITE_API_BASE_URL
    if grep -q "^VITE_API_BASE_URL=" .env; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1|" .env
        else
            sed -i "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1|" .env
        fi
    else
        echo "VITE_API_BASE_URL=http://$LOCAL_IP:8000/api/v1" >> .env
    fi
    
    echo "✅ .env 文件已更新"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 配置完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 手机访问地址："
echo "   前端: http://$LOCAL_IP:5173"
echo "   前端(通过Nginx): http://$LOCAL_IP:80"
echo "   API: http://$LOCAL_IP:8000/api/v1"
echo ""
echo "💡 提示："
echo "   1. 确保手机和电脑在同一 Wi-Fi 网络"
echo "   2. 如果无法访问，检查防火墙设置"
echo "   3. 启动服务：docker-compose -f docker-compose.dev.yml up -d"
echo ""


