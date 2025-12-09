<template>
  <div class="page-container profile-container">
    <van-tabs v-model:active="activeTab">
      <van-tab title="学生管理">
        <div class="students-section">
          <van-loading v-if="loading" vertical>加载中...</van-loading>
          <div v-else>
            <van-empty v-if="students.length === 0" description="暂无学生，请添加" />
            <van-cell-group v-else inset style="margin: 12px;">
              <van-cell
                v-for="student in students"
                :key="student.id"
                :title="student.name"
                :label="getStudentLabel(student)"
                is-link
                @click="editStudent(student)"
              >
                <template #right-icon>
                  <van-icon name="delete-o" @click.stop="handleDeleteStudent(student)" />
                </template>
              </van-cell>
            </van-cell-group>
          </div>
          <div class="add-student-actions">
            <van-button round block type="primary" icon="plus" @click="handleAddStudent">
              新增学生
            </van-button>
          </div>
          <van-floating-bubble
            axis="xy"
            icon="plus"
            @click="handleAddStudent"
          />
        </div>
      </van-tab>
      
      <van-tab title="配置管理">
            <div class="projects-section">
              <van-loading v-if="loadingProjects" vertical>加载中...</van-loading>
              <div v-else>
                <van-cell-group inset style="margin: 12px;">
                  <van-cell title="一级项目" is-link @click="showProject1List = true" />
                  <van-cell title="二级项目" is-link @click="showProject2List = true" />
                </van-cell-group>
                
                <!-- 选项管理 -->
                <van-cell-group inset style="margin: 12px;" title="选项管理">
                  <van-cell title="惩罚选项" is-link @click="openPunishmentOptions" />
                  <van-cell title="兑换奖励选项" is-link @click="openRewardOptions" />
                </van-cell-group>

                <div style="padding: 12px;">
                  <!-- 按钮移至列表内部 -->
                </div>
              </div>
            </div>
      </van-tab>
      
      <van-tab title="设置">
        <van-cell-group inset style="margin: 12px;">
          <van-cell title="退出登录" is-link @click="handleLogout" />
        </van-cell-group>
      </van-tab>
    </van-tabs>

    <!-- 学生表单弹窗 -->
    <van-popup v-model:show="showStudentForm" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        :title="editingStudent ? '编辑学生' : '新增学生'"
        left-arrow
        @click-left="showStudentForm = false"
      />
      <StudentForm
        v-if="showStudentForm"
        :student="editingStudent"
        @success="handleStudentSuccess"
        @cancel="showStudentForm = false"
      />
    </van-popup>

    <!-- 一级项目列表 -->
    <van-popup v-model:show="showProject1List" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="一级项目"
        left-arrow
        @click-left="showProject1List = false"
      />
      <ProjectList level="1" @close="showProject1List = false" />
    </van-popup>

    <!-- 二级项目列表 -->
    <van-popup v-model:show="showProject2List" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="二级项目"
        left-arrow
        @click-left="showProject2List = false"
      />
      <ProjectList level="2" @close="showProject2List = false" />
    </van-popup>

    <!-- 新增一级项目表单 -->
    <van-popup v-model:show="showAddProject1Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增一级项目"
        left-arrow
        @click-left="showAddProject1Form = false"
      />
      <ProjectForm
        v-if="showAddProject1Form"
        :project="null"
        level="1"
        @success="handleProjectSuccess"
        @cancel="showAddProject1Form = false"
      />
    </van-popup>

    <!-- 新增二级项目表单 -->
    <van-popup v-model:show="showAddProject2Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增二级项目"
        left-arrow
        @click-left="showAddProject2Form = false"
      />
      <ProjectForm
        v-if="showAddProject2Form"
        :project="null"
        level="2"
        @success="handleProjectSuccess"
        @cancel="showAddProject2Form = false"
      />
    </van-popup>

    <!-- 惩罚选项列表 -->
    <van-popup v-model:show="showPunishmentOptions" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="惩罚选项"
        left-arrow
        @click-left="showPunishmentOptions = false"
      />
      <PunishmentOptionList v-if="showPunishmentOptions" @close="showPunishmentOptions = false" />
    </van-popup>

    <!-- 兑换奖励选项列表 -->
    <van-popup v-model:show="showRewardOptions" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="兑换奖励选项"
        left-arrow
        @click-left="showRewardOptions = false"
      />
      <RewardOptionList v-if="showRewardOptions" @close="showRewardOptions = false" />
    </van-popup>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showSuccessToast, showFailToast } from 'vant'
import { useAuthStore } from '../stores/auth'
import { useStudentsStore } from '../stores/students'
import { useEnumsStore } from '../stores/enums'
import { studentsApi } from '../api/students'
import { extractErrorMessage } from '../utils/errorHandler'
import StudentForm from '../components/StudentForm.vue'
import ProjectList from '../components/ProjectList.vue'
import ProjectForm from '../components/ProjectForm.vue'
import PunishmentOptionList from '../components/PunishmentOptionList.vue'
import RewardOptionList from '../components/RewardOptionList.vue'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const enumsStore = useEnumsStore()

const loading = ref(false)
const loadingProjects = ref(false)
const students = ref([])
const showStudentForm = ref(false)
const editingStudent = ref(null)
const showProject1List = ref(false)
const showProject2List = ref(false)
const showAddProject1Form = ref(false)
const showAddProject2Form = ref(false)
const showPunishmentOptions = ref(false)
const showRewardOptions = ref(false)
const editingProject = ref(null)
const activeTab = ref(0)
const wasEmptyBeforeAdd = ref(false) // 记录添加前是否为空

const getStudentLabel = (student) => {
  const genderOption = enumsStore.gender.find(g => g.value === student.gender)
  const stageOption = enumsStore.educationStage.find(s => s.value === student.stage)
  const genderText = genderOption ? genderOption.text : student.gender
  const stageText = stageOption ? stageOption.text : student.stage
  return `${genderText} | ${stageText}`
}

const fetchStudents = async () => {
  loading.value = true
  try {
    // 记录添加前的状态
    wasEmptyBeforeAdd.value = students.value.length === 0
    
    await studentsStore.fetchStudents()
    students.value = studentsStore.students
  } catch (error) {
    console.error('加载学生失败:', error)
  } finally {
    loading.value = false
  }
}

const editStudent = (student) => {
  editingStudent.value = student
  showStudentForm.value = true
}

const handleAddStudent = () => {
  editingStudent.value = null
  showStudentForm.value = true
}

const openPunishmentOptions = () => {
  console.log('Opening punishment options')
  showPunishmentOptions.value = true
}

const openRewardOptions = () => {
  console.log('Opening reward options')
  showRewardOptions.value = true
}

const handleStudentSuccess = () => {
  showStudentForm.value = false
  editingStudent.value = null
  
  // 记录添加前的状态
  const wasEmpty = students.value.length === 0
  
  fetchStudents().then(() => {
    // 如果添加前没有学生（从登录页面跳转过来的），添加完学生后跳转到首页
    if (wasEmpty && students.value.length > 0) {
      // 刚添加了第一个学生，跳转到首页
      router.push('/')
    }
  })
}

const handleDeleteStudent = async (student) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除学生"${student.name}"吗？删除后将同时删除该学生的所有任务和积分记录。`,
      confirmButtonText: '删除',
      confirmButtonColor: '#ee0a24',
    })
    
    loading.value = true
    try {
      await studentsApi.delete(student.id)
      showSuccessToast('删除成功')
      await fetchStudents()
    } catch (error) {
      const message = extractErrorMessage(error)
      showFailToast(message)
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消删除
  }
}

const handleLogout = async () => {
  try {
    await showConfirmDialog({
      title: '确认退出',
      message: '确定要退出登录吗？'
    })
    authStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 处理 URL 参数
const handleRouteAction = () => {
  const action = route.query.action
  if (action === 'add-student') {
    // 切换到学生管理标签页
    activeTab.value = 0
    // 打开学生表单
    showStudentForm.value = true
    editingStudent.value = null
    // 清除 URL 参数
    router.replace({ path: '/profile', query: {} })
  }
}

// 监听路由变化
watch(() => route.query.action, () => {
  handleRouteAction()
})

onMounted(() => {
  fetchStudents()
  // 检查是否有 action 参数
  handleRouteAction()
})
</script>

<style scoped>
.profile-container {
  width: 100%;
}

.students-section,
.projects-section {
  padding: 12px;
}

.add-student-actions {
  padding: 12px;
}

@media (min-width: 768px) {
  .students-section,
  .projects-section {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .students-section,
  .projects-section {
    padding: 24px;
    max-width: 1000px;
    margin: 0 auto;
  }
}
</style>

