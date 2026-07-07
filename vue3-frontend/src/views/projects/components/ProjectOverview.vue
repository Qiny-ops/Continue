<template>
  <div class="project-overview">
    <!-- 项目头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="project-icon" :style="{ background: project?.iconColor || 'var(--color-primary)' }">
            <el-icon :size="24"><Folder /></el-icon>
          </div>
          <div class="project-info">
            <h1 class="project-name">{{ project?.name || '未命名项目' }}</h1>
            <div class="project-tags">
              <el-tag :type="getStatusType(project?.status)" size="small">
                {{ getStatusLabel(project?.status) }}
              </el-tag>
              <el-tag type="info" size="small">{{ getTypeLabel(project?.type) }}</el-tag>
            </div>
          </div>
        </div>
        <div class="header-right">
          <router-link :to="`/p/${project?.code}/testcases`" class="header-btn primary">
            <el-icon><Document /></el-icon>
            进入用例
          </router-link>
          <router-link :to="`/p/${project?.code}/settings`" class="header-btn">
            <el-icon><Setting /></el-icon>
            项目设置
          </router-link>
        </div>
      </div>
    </header>

    <!-- 数据统计 -->
    <section class="stats-section">
      <div class="stats-card" @click="$router.push(`/p/${project?.code}/testcases`)">
        <div class="stats-icon blue">
          <el-icon :size="20"><Document /></el-icon>
        </div>
        <div class="stats-body">
          <div class="stats-value">{{ project?.testCases || 0 }}</div>
          <div class="stats-label">测试用例</div>
        </div>
        <div class="stats-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon green">
          <el-icon :size="20"><Collection /></el-icon>
        </div>
        <div class="stats-body">
          <div class="stats-value">{{ stats.repositories }}</div>
          <div class="stats-label">用例库</div>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon purple">
          <el-icon :size="20"><Files /></el-icon>
        </div>
        <div class="stats-body">
          <div class="stats-value">{{ stats.versions }}</div>
          <div class="stats-label">版本</div>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon orange">
          <el-icon :size="20"><Grid /></el-icon>
        </div>
        <div class="stats-body">
          <div class="stats-value">{{ stats.modules }}</div>
          <div class="stats-label">模块</div>
        </div>
      </div>
    </section>

    <!-- 内容区域 -->
    <main class="page-content">
      <div class="content-grid">
        <!-- 项目详情 -->
        <div class="content-panel">
          <div class="panel-header">
            <div class="panel-title">
              <el-icon><InfoFilled /></el-icon>
              项目详情
            </div>
            <router-link :to="`/p/${project?.code}/settings`" class="panel-link">
              编辑
            </router-link>
          </div>
          <div class="panel-body">
            <div class="detail-list">
              <div class="detail-item">
                <span class="detail-label">项目标识</span>
                <span class="detail-value code">{{ project?.code || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">项目负责人</span>
                <span class="detail-value">{{ project?.owner || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">项目周期</span>
                <span class="detail-value">{{ formatDate(project?.startTime) || '未设置' }} — {{ formatDate(project?.endTime) || '未设置' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">创建时间</span>
                <span class="detail-value">{{ formatDateTime(project?.createdAt) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">更新时间</span>
                <span class="detail-value">{{ formatDateTime(project?.updatedAt) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 最近动态 -->
        <div class="content-panel">
          <div class="panel-header">
            <div class="panel-title">
              <el-icon><Clock /></el-icon>
              最近动态
            </div>
          </div>
          <div class="panel-body">
            <div v-if="activitiesLoading" class="loading-wrap">
              <el-icon class="is-loading" :size="20"><Loading /></el-icon>
            </div>
            <div v-else-if="activities.length === 0" class="empty-wrap">
              <span>暂无动态记录</span>
            </div>
            <div v-else class="activity-list">
              <div v-for="activity in activities" :key="activity.id" class="activity-item">
                <div class="activity-icon" :class="activity.type">
                  <el-icon :size="12">
                    <component :is="getActivityIcon(activity.type)" />
                  </el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-title">
                    <span class="activity-user">{{ activity.userName || '用户' }}</span>
                    {{ getActivityAction(activity.type) }}
                    <span class="activity-target">{{ activity.targetName }}</span>
                  </div>
                  <div class="activity-time">{{ formatActivityTime(activity.createdAt) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 团队成员 -->
        <div class="content-panel">
          <div class="panel-header">
            <div class="panel-title">
              <el-icon><UserFilled /></el-icon>
              团队成员
              <span class="member-count">{{ members.length }}</span>
            </div>
            <router-link :to="`/p/${project?.code}/settings?tab=members`" class="panel-link">
              管理
            </router-link>
          </div>
          <div class="panel-body">
            <div v-if="membersLoading" class="loading-wrap">
              <el-icon class="is-loading" :size="20"><Loading /></el-icon>
            </div>
            <div v-else-if="members.length === 0" class="empty-wrap">
              <span>暂无成员</span>
            </div>
            <div v-else class="member-list">
              <div v-for="member in members.slice(0, 6)" :key="member.id" class="member-item">
                <div class="member-avatar" :style="{ background: getAvatarColor(member.name) }">
                  {{ getInitial(member.name) }}
                </div>
                <div class="member-body">
                  <span class="member-name">{{ member.name }}</span>
                  <span class="member-role" :class="member.role">{{ getRoleLabel(member.role) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import {
  Folder, Document, Setting, Collection, Files, Grid,
  ArrowRight, InfoFilled, Clock,
  UserFilled, Loading, Edit, Delete, View, Plus
} from '@element-plus/icons-vue'
import { getStatusLabel, getStatusType } from '@/constants/project.js'
import memberApi from '@/api/modules/member'
import projectApi from '@/api/modules/project'

const props = defineProps({
  project: {
    type: Object,
    default: () => ({})
  }
})

const members = ref([])
const membersLoading = ref(false)
const activities = ref([])
const activitiesLoading = ref(false)

const stats = computed(() => ({
  repositories: props.project?.repositories || 0,
  versions: props.project?.versions || 0,
  modules: props.project?.modules || 0
}))

const getTypeLabel = (type) => {
  const labels = {
    web: 'Web项目',
    mobile: '移动应用',
    api: 'API项目',
    desktop: '桌面应用',
    performance: '性能测试',
    security: '安全测试',
    other: '其他'
  }
  return labels[type] || '项目'
}

const getRoleLabel = (role) => {
  const labels = {
    admin: '管理员',
    developer: '开发',
    tester: '测试',
    viewer: '观察者'
  }
  return labels[role] || role
}

const getActivityIcon = (type) => {
  const icons = {
    create: Plus,
    update: Edit,
    delete: Delete,
    view: View
  }
  return icons[type] || Document
}

const getActivityAction = (type) => {
  const actions = {
    create: '创建了',
    update: '更新了',
    delete: '删除了',
    view: '查看了'
  }
  return actions[type] || '操作了'
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

const formatDateTime = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatActivityTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const getAvatarColor = (name) => {
  const colors = ['var(--color-primary)', 'var(--color-success)', 'var(--color-warning)', 'var(--color-danger)', 'var(--color-info)', 'var(--color-danger)']
  const index = name ? name.charCodeAt(0) % colors.length : 0
  return colors[index]
}

const getInitial = (name) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

const fetchMembers = async () => {
  if (!props.project?.code) return
  membersLoading.value = true
  try {
    const res = await memberApi.getMembers(props.project.code)
    if (res?.data) {
      members.value = res.data.members || res.data || []
    }
  } catch {
  } finally {
    membersLoading.value = false
  }
}

const fetchActivities = async () => {
  if (!props.project?.code) return
  activitiesLoading.value = true
  try {
    const res = await projectApi.getProjectActivities(props.project.code)
    if (res?.data) {
      activities.value = res.data.activities || res.data || []
    }
  } catch {
    activities.value = [
      { id: 1, type: 'create', userName: '管理员', targetName: '测试用例库', createdAt: new Date(Date.now() - 3600000) },
      { id: 2, type: 'update', userName: '测试人员', targetName: '登录模块用例', createdAt: new Date(Date.now() - 7200000) },
      { id: 3, type: 'view', userName: '开发人员', targetName: '项目概览', createdAt: new Date(Date.now() - 86400000) }
    ]
  } finally {
    activitiesLoading.value = false
  }
}

watch(() => props.project?.code, (newCode) => {
  if (newCode) {
    fetchMembers()
    fetchActivities()
  }
})

onMounted(() => {
  fetchMembers()
  fetchActivities()
})
</script>

<style scoped>
.project-overview {
  height: 100%;
  overflow-y: auto;
}

/* Hero 区域 */
.page-header {
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-icon {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.project-tags {
  display: flex;
  gap: 6px;
}

.header-right {
  display: flex;
  gap: 8px;
}

.header-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 2px;
  text-decoration: none;
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-primary);
  transition: all 0.2s ease;
}

.header-btn:hover {
  background: var(--color-border-primary);
}

.header-btn.primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.header-btn.primary:hover {
  background: var(--color-primary-hover);
}

/* 统计卡片 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
}

.stats-card {
  background: var(--color-bg-secondary);
  border-radius: 2px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--color-border-primary);
  transition: all 0.2s ease;
  cursor: default;
}

.stats-card:first-child {
  cursor: pointer;
}

.stats-card:hover {
  border-color: var(--color-primary);
}

.stats-icon {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stats-icon.blue {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.stats-icon.green {
  background: var(--color-success-light);
  color: var(--color-success);
}

.stats-icon.purple {
  background: var(--color-info-light);
  color: var(--color-info);
}

.stats-icon.orange {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.stats-body {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1;
}

.stats-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.stats-arrow {
  color: var(--color-text-secondary);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.stats-card:first-child:hover .stats-arrow {
  opacity: 1;
  color: var(--color-primary);
}

/* 内容区域 */
.page-content {
  background: var(--color-bg-secondary);
  padding: 16px 24px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

.content-panel {
  background: #fff;
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-title .el-icon {
  color: var(--color-text-secondary);
}

.member-count {
  margin-left: 6px;
  padding: 1px 6px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 500;
  border-radius: 2px;
}

.panel-link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
}

.panel-link:hover {
  color: var(--color-primary-hover);
}

.panel-body {
  padding: 12px 16px;
}

/* 详情列表 */
.detail-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-bg-secondary);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.detail-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.detail-value.code {
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
  font-family: monospace;
  font-size: 12px;
  font-weight: 400;
}

/* 动态列表 */
.activity-list {
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-bg-secondary);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.activity-icon.create {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.activity-icon.update {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.activity-icon.delete {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.activity-icon.view {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.activity-user {
  color: var(--color-text-primary);
  font-weight: 500;
}

.activity-target {
  color: var(--color-primary);
  font-weight: 500;
}

.activity-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* 成员列表 */
.member-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.member-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.member-role {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.member-role.admin {
  color: var(--color-danger);
}

/* 加载和空状态 */
.loading-wrap,
.empty-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.loading-wrap .el-icon {
  color: var(--color-primary);
}

/* 响应式 */
@media (max-width: 1400px) {
  .content-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1200px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    height: auto;
    padding: 12px 16px;
    gap: 12px;
  }

  .header-right {
    width: 100%;
  }

  .header-btn {
    flex: 1;
    justify-content: center;
  }

  .stats-section {
    grid-template-columns: 1fr;
    padding: 12px 16px;
  }

  .page-content {
    padding: 12px 16px;
  }
}
</style>