/**
 * 提供按名称动态获取 Element Plus 图标组件的工具函数
 * 只有实际被引用的图标才会被打包，避免 import * 导致全量加载
 */
import {
  Folder, FolderOpened, Document, Monitor, Cellphone,
  Connection, DataAnalysis, Setting, User, Calendar,
  Briefcase, Box, Star, View, Delete, Search, Edit,
  Plus, UserFilled, InfoFilled, CircleCheckFilled,
  Grid, DataBoard, Picture, Tools, Lock, Unlock,
  Key, MagicStick, Cpu, Platform, Link, Trophy,
  Flag, Medal, ChatDotRound, Service, ArrowRight,
  ArrowLeft, WarningFilled, Loading, Clock
} from '@element-plus/icons-vue'

const iconMap = {
  Folder, FolderOpened, Document, Monitor, Cellphone,
  Connection, DataAnalysis, Setting, User, Calendar,
  Briefcase, Box, Star, View, Delete, Search, Edit,
  Plus, UserFilled, InfoFilled, CircleCheckFilled,
  Grid, DataBoard, Picture, Tools, Lock, Unlock,
  Key, MagicStick, Cpu, Platform, Link, Trophy,
  Flag, Medal, ChatDotRound, Service, ArrowRight,
  ArrowLeft, WarningFilled, Loading, Clock
}

export function getIconComponent(name) {
  return iconMap[name] || Folder
}

export const roleIcons = [
  { name: 'Folder', label: '文件夹', component: Folder },
  { name: 'Document', label: '文档', component: Document },
  { name: 'Monitor', label: '显示器', component: Monitor },
  { name: 'Cellphone', label: '手机', component: Cellphone },
  { name: 'Connection', label: '连接', component: Connection },
  { name: 'DataAnalysis', label: '数据分析', component: DataAnalysis },
  { name: 'Setting', label: '设置', component: Setting },
  { name: 'User', label: '用户', component: User },
  { name: 'Calendar', label: '日历', component: Calendar },
  { name: 'Briefcase', label: '公文包', component: Briefcase },
  { name: 'Box', label: '盒子', component: Box },
  { name: 'Star', label: '星星', component: Star }
]

export const projectIcons = [
  { name: 'Folder', label: '文件夹', component: Folder },
  { name: 'Document', label: '文档', component: Document },
  { name: 'Monitor', label: '显示器', component: Monitor },
  { name: 'DataBoard', label: '数据看板', component: DataBoard },
  { name: 'Connection', label: '连接', component: Connection },
  { name: 'Platform', label: '平台', component: Platform },
  { name: 'Briefcase', label: '公文包', component: Briefcase },
  { name: 'Cellphone', label: '手机', component: Cellphone },
  { name: 'Tools', label: '工具', component: Tools },
  { name: 'Star', label: '星星', component: Star },
  { name: 'DataAnalysis', label: '数据分析', component: DataAnalysis },
  { name: 'Cpu', label: 'CPU', component: Cpu }
]