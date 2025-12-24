# 积分管理 - 前端

## 技术栈

- Vue 3
- Vite
- Vant 4 (移动端 UI 组件库)
- Vue Router 4
- Pinia (状态管理)
- Axios (HTTP 客户端)

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 项目结构

```
src/
├── api/           # API 接口
├── components/    # 组件
├── router/        # 路由配置
├── stores/        # Pinia 状态管理
├── views/         # 页面组件
└── main.js        # 入口文件
```

## 主要功能

- 用户注册/登录
- 学生管理
- 项目管理（一级/二级）
- 任务管理
- 积分管理（汇总、增加记录、兑换记录）
- 首页数据展示
- 管理员功能
