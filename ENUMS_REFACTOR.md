# 枚举值统一管理重构

## 目标
将所有固定的下拉框选项从后端统一获取，保持前后端一致，修改时只需改动一处。

## 实现方案

### 后端
1. **创建枚举 API 端点** (`app/api/v1/endpoints/enums.py`)
   - `GET /api/v1/enums/enums` - 返回所有枚举值
   - 包含的枚举类型：
     - `task_status` - 任务状态
     - `task_rating` - 任务评分
     - `reward_type` - 惩奖类型
     - `reward_points` - 奖励积分选项
     - `gender` - 性别
     - `education_stage` - 教育阶段
     - `project_level` - 项目层级

### 前端
1. **创建枚举 Store** (`frontend/src/stores/enums.js`)
   - 使用 Pinia 管理枚举值
   - 提供计算属性方便使用
   - 应用启动时自动加载

2. **更新组件**
   - `TaskForm.vue` - 任务表单
   - `Tasks.vue` - 任务列表
   - `StudentForm.vue` - 学生表单
   - 所有硬编码的枚举值改为从 store 获取

## 枚举值列表

### 任务状态 (task_status)
- 未开始 (not_started)
- 进行中 (in_progress)
- 已完成 (completed)
- 已取消 (canceled)

### 任务评分 (task_rating)
- A*
- A
- A-
- B
- B-
- C

### 惩奖类型 (reward_type)
- 无 (none)
- 奖励 (reward)
- 惩罚 (punish)

### 奖励积分 (reward_points)
- 1积分
- 3积分
- 5积分
- 7积分
- 10积分

### 性别 (gender)
- 男 (male)
- 女 (female)

### 教育阶段 (education_stage)
- 小学 (primary)
- 初中 (middle)

### 项目层级 (project_level)
- 一级项目 (1)
- 二级项目 (2)

## 使用方法

### 后端修改枚举值
编辑 `app/api/v1/endpoints/enums.py` 中的 `get_enums()` 函数，修改对应的枚举值列表。

### 前端使用枚举值
```javascript
import { useEnumsStore } from '../stores/enums'

const enumsStore = useEnumsStore()

// 获取任务状态选项
const statusColumns = computed(() => enumsStore.taskStatus)

// 获取任务评分选项
const ratingColumns = computed(() => enumsStore.taskRating)

// 获取性别选项
const genderColumns = computed(() => enumsStore.gender)
```

## 优势
1. **单一数据源** - 所有枚举值统一在后端管理
2. **前后端一致** - 避免前后端枚举值不一致的问题
3. **易于维护** - 修改时只需改动后端一处
4. **类型安全** - 使用 TypeScript/Pydantic 确保类型正确

