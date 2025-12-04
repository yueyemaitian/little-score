# ===========================================
# Nginx 反向代理 Dockerfile
# ===========================================
FROM nginx:alpine

LABEL maintainer="Little Score Team"
LABEL description="Nginx reverse proxy for Little Score"

# 安装工具
RUN apk add --no-cache \
    curl \
    openssl \
    tzdata

# 设置时区
ENV TZ=Asia/Shanghai
RUN cp /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 删除默认配置
RUN rm -rf /etc/nginx/conf.d/default.conf

# 复制主配置文件
COPY nginx.conf /etc/nginx/nginx.conf

# 复制站点配置
COPY conf.d/ /etc/nginx/conf.d/

# 创建 SSL 证书目录（生产环境使用）
RUN mkdir -p /etc/nginx/ssl

# 创建日志目录并设置权限
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# 创建缓存目录
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx

# 注意：不在构建时验证配置，因为 upstream 主机名只有在运行时才能解析
# 配置验证将在容器启动时自动执行

# 暴露端口
EXPOSE 80 443

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || wget -q --spider http://localhost/health || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]

