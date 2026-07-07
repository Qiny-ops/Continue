/**
 * 项目相关常量和实体定义
 */

// ==================== 页面配置 ====================

export const PROJECT_TABS = [
  { key: 'projects', label: '我参与的' },
  { key: 'managed', label: '我管理的' }
]

export const PROJECT_TABLE_COLUMNS = [
  { prop: 'name', label: '项目', flexGrow: 1, minWidth: 200 },
  { prop: 'type', label: '类型', width: 100, flexShrink: 0 },
  { prop: 'status', label: '状态', width: 100, flexShrink: 0 },
  { prop: 'stats', label: '统计', width: 200, flexShrink: 0 },
  { prop: 'owner', label: '负责人', width: 120, flexShrink: 0 },
  { prop: 'favorite', label: '收藏', width: 60, flexShrink: 0 },
  { prop: 'actions', label: '操作', width: 44, flexShrink: 0 }
]

export const DEFAULT_AVATAR_URL = 'https://coding-net-production-static-ci.codehub.cn/d190f420-ee82-4251-b5e3-da67c8e0e2ba.jpg?imageMogr2/cut/800x800x0x0'

// ==================== 类型映射 ====================

export const PROJECT_TYPE_MAP = {
  web: { label: 'Web项目', type: 'primary' },
  mobile: { label: '移动应用', type: 'success' },
  api: { label: 'API项目', type: 'warning' },
  desktop: { label: '桌面应用', type: 'info' },
  performance: { label: '性能测试', type: 'danger' },
  security: { label: '安全测试', type: 'danger' },
  other: { label: '其他', type: '' }
}

export const PROJECT_STATUS_MAP = {
  active: { label: '进行中', type: 'success' },
  completed: { label: '已完成', type: 'primary' },
  pending: { label: '待开始', type: 'warning' },
  archived: { label: '已归档', type: 'info' }
}

// ==================== 枚举定义 ====================

export const ProjectStatus = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  PENDING: 'pending',
  ARCHIVED: 'archived'
}

export const ProjectType = {
  WEB: 'web',
  MOBILE: 'mobile',
  API: 'api',
  DESKTOP: 'desktop',
  PERFORMANCE: 'performance',
  SECURITY: 'security',
  OTHER: 'other'
}

const ICON_MAP = {
  [ProjectType.WEB]: 'monitor',
  [ProjectType.MOBILE]: 'iphone',
  [ProjectType.API]: 'link',
  [ProjectType.DESKTOP]: 'monitor',
  [ProjectType.PERFORMANCE]: 'trend-charts',
  [ProjectType.SECURITY]: 'lock',
  [ProjectType.OTHER]: 'folder'
}

// ==================== 工具函数 ====================

export const getProjectTypeLabel = (type) =>
  PROJECT_TYPE_MAP[type]?.label || '其他'

export const getProjectTypeType = (type) =>
  PROJECT_TYPE_MAP[type]?.type || ''

export const getStatusLabel = (status) =>
  PROJECT_STATUS_MAP[status]?.label || '未知'

export const getStatusType = (status) =>
  PROJECT_STATUS_MAP[status]?.type || ''

// ==================== 项目实体类 ====================

export class Project {
  constructor(data = {}) {
    this.id = this._normalizeId(data.id)
    this.name = this._normalizeString(data.name)
    this.code = this._normalizeString(data.code)
    this.identifier = this._normalizeString(data.identifier || data.code)
    this.description = this._normalizeString(data.description)
    this.type = this._normalizeType(data.type)
    this.status = this._normalizeStatus(data.status)
    this.visibility = this._normalizeString(data.visibility || 'public')
    this.icon = this._normalizeString(data.icon || 'Folder')
    this.iconColor = this._normalizeString(data.iconColor || '#3b82f6')
    this.startTime = this._normalizeString(data.startTime || data.start_time || '')
    this.endTime = this._normalizeString(data.endTime || data.end_time || '')
    this.createdAt = this._normalizeDate(data.createdAt || data.created_at || data.createTime)
    this.updatedAt = this._normalizeDate(data.updatedAt || data.updated_at || data.updateTime)
    this.settings = this._normalizeObject(data.settings)

    this.owner = this._normalizeString(data.owner?.name || data.owner?.username || data.owner_name || data.owner || '未知用户')
    this.ownerAvatar = this._normalizeString(data.owner?.avatar || data.ownerAvatar || data.owner_avatar || '')
    this.createdBy = this._normalizeString(data.createdBy?.name || data.createdBy?.username || data.created_by_name || data.createdBy || data.created_by || this.owner)
    this.createdByAvatar = this._normalizeString(data.createdBy?.avatar || data.createdByAvatar || data.created_by_avatar || '')
    this.admins = Array.isArray(data.admins) ? data.admins : []
    this.isFavorite = Boolean(data.isFavorite)
    this.isAdmin = Boolean(data.isAdmin)
    this.isOwner = Boolean(data.isOwner)
    this.role = this._normalizeString(data.role || 'viewer')
    this.testCases = this._normalizeNumber(data.testCases || data.testCaseCount)
    this.testPlans = this._normalizeNumber(data.testPlans)
    this.bugs = this._normalizeNumber(data.bugs)
    this.knowledgeBaseId = this._normalizeString(data.knowledgeBaseId || data.knowledge_base_id || '')
    this.knowledgeBaseName = this._normalizeString(data.knowledgeBaseName || data.knowledge_base_name || '')
  }

  _normalizeId(id) { return id || null }
  _normalizeString(value) { return String(value || '') }
  _normalizeNumber(value) { const num = Number(value); return isNaN(num) ? 0 : num }
  _normalizeDate(value) {
    if (!value) return new Date().toISOString()
    if (value instanceof Date) return value.toISOString()
    return String(value)
  }
  _normalizeObject(value) { return typeof value === 'object' && value !== null ? value : {} }
  _normalizeType(type) {
    const validTypes = Object.values(ProjectType)
    return validTypes.includes(type) ? type : ProjectType.WEB
  }
  _normalizeStatus(status) {
    const validStatuses = Object.values(ProjectStatus)
    return validStatuses.includes(status) ? status : ProjectStatus.ACTIVE
  }

  getIcon() { return ICON_MAP[this.type] || 'folder' }
  isActive() { return this.status === ProjectStatus.ACTIVE }
  isCompleted() { return this.status === ProjectStatus.COMPLETED }
  isPending() { return this.status === ProjectStatus.PENDING }
  isArchived() { return this.status === ProjectStatus.ARCHIVED }

  toJSON() {
    return {
      id: this.id, name: this.name, code: this.code, identifier: this.identifier,
      description: this.description, type: this.type, status: this.status,
      visibility: this.visibility, iconColor: this.iconColor, startTime: this.startTime,
      endTime: this.endTime, createdAt: this.createdAt, updatedAt: this.updatedAt,
      createdBy: this.createdBy, settings: this.settings, icon: this.icon,
      owner: this.owner, ownerAvatar: this.ownerAvatar, createdByAvatar: this.createdByAvatar,
      isFavorite: this.isFavorite, isAdmin: this.isAdmin, isOwner: this.isOwner, role: this.role,
      testCases: this.testCases, testPlans: this.testPlans, bugs: this.bugs,
      knowledgeBaseId: this.knowledgeBaseId, knowledgeBaseName: this.knowledgeBaseName
    }
  }

  static fromJSON(data) { return new Project(data) }
}

export default {
  PROJECT_TABS,
  PROJECT_TABLE_COLUMNS,
  DEFAULT_AVATAR_URL,
  PROJECT_TYPE_MAP,
  PROJECT_STATUS_MAP,
  ProjectStatus,
  ProjectType,
  Project,
  getProjectTypeLabel,
  getProjectTypeType,
  getStatusLabel,
  getStatusType
}
