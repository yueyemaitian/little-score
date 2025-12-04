# Little Score 学生积分管理系统

本项目是一个面向家长和孩子的任务积分管理系统，支持手机浏览器和微信内打开访问。

## 技术栈

### 后端
- FastAPI
- SQLAlchemy 2.0 + Alembic
- Pydantic
- Passlib (密码哈希)
- Python-JOSE (JWT认证)
- MySQL (使用 aiomysql)

### 前端
- Vue 3 + Vite
- Vue Router 4
- Pinia (状态管理)
- Vant 4 (移动端 UI 组件库)
- Axios (HTTP 客户端)

### 部署
- Nginx 反向代理
- PM2 (进程管理)
- Docker

## 项目结构

```
little-score/
├── app/                    # 后端应用
│   ├── api/               # API 路由
│   │   └── v1/
│   │       ├── endpoints/ # API 端点
│   │       └── api.py     # 路由聚合
│   ├── core/              # 核心配置
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic 模型
│   ├── crud/              # CRUD 操作
│   ├── db/                # 数据库配置
│   └── main.py            # 应用入口
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 接口
│   │   ├── components/    # 组件
│   │   ├── router/        # 路由
│   │   ├── stores/        # Pinia 状态
│   │   └── views/         # 页面
│   └── package.json
├── alembic/                # 数据库迁移
├── requirements.txt        # Python 依赖
└── README.md
```

## 快速开始

### 1. 后端设置

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置环境变量
创建 `.env` 文件：
```env
SQLALCHEMY_DATABASE_URI=mysql+aiomysql://user:password@127.0.0.1:3306/little_score
SECRET_KEY=your-secret-key-here
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

#### 初始化数据库
```bash
# 创建迁移
python3 -m alembic revision --autogenerate -m "Initial migration"

# 运行迁移
python3 -m alembic upgrade head

# 初始化系统设置
python3 -m app.db.init_db
```

#### 启动后端服务
```bash
python3 -m uvicorn app.main:app --reload
```

后端服务运行在 http://localhost:8000
API 文档: http://localhost:8000/docs

### 2. 前端设置

#### 安装依赖
```bash
cd frontend
npm install
```

#### 配置环境变量
创建 `frontend/.env` 文件：
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### 启动开发服务器
```bash
npm run dev
```

前端服务运行在 http://localhost:5173

## 功能特性

### 用户功能
- ✅ 用户注册/登录（邮箱+密码）
- ✅ 学生管理（添加、修改学生信息）
- ✅ 项目管理（一级/二级项目自定义）
- ✅ 任务管理（创建、修改任务，状态流转）
- ✅ 积分管理（积分汇总、增加记录、兑换记录）
- ✅ 首页数据展示（学生列表、积分汇总、任务评分统计）

### 管理员功能
- ✅ 用户列表查看
- ✅ 系统设置（是否允许注册）

### 核心业务逻辑
- ✅ 任务完成时自动生成积分增加记录
- ✅ 惩罚任务自动生成关联任务
- ✅ 积分兑换时自动校验可用积分
- ✅ 系统注册开关控制

## API 端点

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户

### 学生管理
- `GET /api/v1/students/` - 获取学生列表
- `POST /api/v1/students/` - 创建学生
- `PUT /api/v1/students/{id}` - 更新学生

### 项目管理
- `GET /api/v1/projects/` - 获取项目列表
- `POST /api/v1/projects/` - 创建项目
- `PUT /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目

### 任务管理
- `GET /api/v1/tasks/` - 获取任务列表
- `POST /api/v1/tasks/` - 创建任务
- `PUT /api/v1/tasks/{id}` - 更新任务

### 积分管理
- `GET /api/v1/scores/summary` - 积分汇总
- `GET /api/v1/scores/increases` - 积分增加记录
- `GET /api/v1/scores/exchanges` - 积分兑换记录
- `POST /api/v1/scores/exchanges` - 创建兑换记录
- `GET /api/v1/scores/reward-options` - 奖励选项列表
- `POST /api/v1/scores/reward-options` - 创建奖励选项
- `GET /api/v1/scores/punishment-options` - 惩罚选项列表
- `POST /api/v1/scores/punishment-options` - 创建惩罚选项

### 首页
- `GET /api/v1/dashboard/` - 获取首页数据

### 管理员
- `GET /api/v1/admin/settings` - 获取系统设置
- `PUT /api/v1/admin/settings` - 更新系统设置
- `GET /api/v1/users/` - 获取用户列表

## 开发

### 后端开发
```bash
# 创建新的数据库迁移
python3 -m alembic revision --autogenerate -m "描述"

# 应用迁移
python3 -m alembic upgrade head

# 回退迁移
python3 -m alembic downgrade -1
```

### 前端开发
```bash
cd frontend
npm run dev
```

## 部署

详细的部署文档请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)

### 快速部署（Docker Compose）

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### PM2 部署（仅后端）

```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

## 许可证

MIT
