# ===========================================
# 前端 Dockerfile (Vue 3 + Vite)
# 支持开发和生产两种模式
# ===========================================

# =================== 开发阶段 ===================
FROM node:alpine AS development

LABEL maintainer="Little Score Team"
LABEL description="Frontend development server for Little Score"

WORKDIR /app

# 安装基础工具
RUN apk add --no-cache curl

# 复制 package 文件
COPY package*.json ./

# 安装依赖（包含 devDependencies）
RUN npm ci

# 复制源代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露 Vite 开发服务器端口
EXPOSE 5173

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# 开发环境启动命令（热更新）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =================== 构建阶段 ===================
FROM node:alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# =================== 生产阶段 ===================
FROM nginx:alpine AS production

LABEL maintainer="Little Score Team"
LABEL description="Frontend production server for Little Score"

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 删除默认配置
RUN rm -rf /etc/nginx/conf.d/default.conf

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建日志目录并设置权限
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
