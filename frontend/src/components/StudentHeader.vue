<template>
  <div>
    <!-- 顶部 App 头部（点击可选择/新增孩子） -->
    <div class="home-header" @click="openStudentPicker">
      <div class="header-left">
        <div class="header-avatar" :style="{ backgroundImage: `url(${getAvatarUrl()})` }">
        </div>
        <div class="header-info" v-if="student">
          <div class="header-name">{{ student.name }}</div>
          <div class="header-meta">
            {{ getGradeDisplay(student) }}
          </div>
        </div>
        <van-icon name="arrow-down" class="header-arrow" />
      </div>
    </div>

    <!-- 孩子下拉选择 / 新增 -->
    <van-popup v-model:show="showPicker" position="bottom" round>
      <van-picker
        title="选择孩子"
        :columns="studentColumns"
        @confirm="onConfirm"
        @cancel="showPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  student: {
    type: Object,
    default: null
  },
  allStudents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['switch', 'add'])
const router = useRouter()
const showPicker = ref(false)

// 根据性别返回头像文件路径
const getAvatarUrl = () => {
  if (!props.student || !props.student.gender) {
    return '/avatar-default-40x40.png' // 默认头像
  }
  
  if (props.student.gender === 'male') {
    return '/avatar-boy-40x40.png' // 男孩头像
  }
  
  if (props.student.gender === 'female') {
    return '/avatar-girl-40x40.png' // 女孩头像
  }
  
  return '/avatar-default-40x40.png'
}

// 计算并显示年级
const getGradeDisplay = (student) => {
  if (!student) return '年级未设置'
  
  // 获取学校名称
  const school = student.school
  
  // 如果没有入学日期或教育阶段
  if (!student.enroll_date || !student.stage) {
    // 如果学校为空，返回默认文本
    return school || '年级未设置'
  }
  
  try {
    // 解析入学日期
    const enrollDate = new Date(student.enroll_date)
    const enrollYear = enrollDate.getFullYear()
    
    // 获取当前日期
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth() + 1 // getMonth() 返回 0-11
    
    // 计算年级：当前年份 - 入学年份
    let grade = currentYear - enrollYear
    
    // 如果当前月份在9月及以后，年级+1
    if (currentMonth >= 9) {
      grade += 1
    }
    
    // 确保年级至少为1
    if (grade < 1) {
      grade = 1
    }
    
    // 根据教育阶段显示
    let gradeText = ''
    if (student.stage === 'primary') {
      // 小学最多6年级
      if (grade > 6) {
        grade = 6
      }
      // 小学：小一、小二、小三、小四、小五、小六
      const gradeMap = ['', '一', '二', '三', '四', '五', '六']
      gradeText = `小${gradeMap[grade] || grade}`
    } else if (student.stage === 'junior_high') {
      // 初中最多3年级
      if (grade > 3) {
        grade = 3
      }
      // 初中：初一、初二、初三
      const gradeMap = ['', '一', '二', '三']
      gradeText = `初${gradeMap[grade] || grade}`
    } else {
      // 未知教育阶段
      const gradeDisplay = `第${grade}年级`
      // 如果学校为空，只显示年级
      return school ? `${school} · ${gradeDisplay}` : gradeDisplay
    }
    
    // 如果学校为空，只显示年级
    return school ? `${school} · ${gradeText}` : gradeText
  } catch (error) {
    console.error('计算年级失败:', error)
    return school || '年级未设置'
  }
}

// 孩子选择下拉选项：所有孩子 + "＋ 添加孩子"
const studentColumns = computed(() => {
  const base = props.allStudents.map((item) => ({
    text: item.name,
    value: item.id
  }))
  return [
    ...base,
    {
      text: '＋ 添加孩子',
      value: 'add'
    }
  ]
})

// 打开孩子选择下拉
const openStudentPicker = () => {
  if (!props.allStudents.length) {
    emit('add')
    return
  }
  showPicker.value = true
}

// 下拉确认选择
const onConfirm = ({ selectedOptions }) => {
  const option = selectedOptions?.[0]
  if (!option) {
    showPicker.value = false
    return
  }
  if (option.value === 'add') {
    showPicker.value = false
    emit('add')
    return
  }
  emit('switch', option.value)
  showPicker.value = false
}
</script>

<style scoped>
.home-header {
  padding: 10px 12px 6px;
  padding-top: calc(12px + env(safe-area-inset-top));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.header-info {
  display: flex;
  flex-direction: column;
}

.header-arrow {
  font-size: 14px;
  color: #9ca3af;
  margin-left: 4px;
}

.header-name {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
}

.header-meta {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}
</style>
