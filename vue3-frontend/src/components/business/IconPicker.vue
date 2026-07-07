<template>
  <div class="icon-picker">
    <div class="icon-preview-wrapper" @click="openPicker">
      <div class="icon-preview" :style="{ backgroundColor: color }">
        <el-icon :size="28">
          <component :is="currentIcon" />
        </el-icon>
      </div>
      <div class="preview-info">
        <span class="preview-label">项目图标</span>
        <span class="preview-name">{{ modelValue }}</span>
      </div>
      <el-icon class="edit-icon"><Edit /></el-icon>
    </div>
    
    <el-dialog
      v-model="visible"
      title="选择项目图标"
      width="680px"
      :close-on-click-modal="false"
      class="icon-picker-dialog"
    >
      <div class="picker-container">
        <div class="picker-sidebar">
          <div
            v-for="cat in iconCategories"
            :key="cat.key"
            :class="['sidebar-item', { active: activeCategory === cat.key }]"
            @click="activeCategory = cat.key"
          >
            <el-icon :size="18"><component :is="cat.icon" /></el-icon>
            <span>{{ cat.label }}</span>
          </div>
        </div>
        
        <div class="picker-main">
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索图标..."
              :prefix-icon="Search"
              clearable
              size="large"
            />
          </div>
          
          <div class="icon-grid-container">
            <div class="icon-grid">
              <div
                v-for="item in filteredIcons"
                :key="item.name"
                :class="['icon-item', { selected: tempSelected === item.name }]"
                @click="selectIcon(item.name)"
              >
                <div class="icon-item-inner" :style="{ backgroundColor: color }">
                  <el-icon :size="24">
                    <component :is="item.component" />
                  </el-icon>
                </div>
                <span class="icon-item-name">{{ item.label }}</span>
              </div>
            </div>
            
            <div v-if="filteredIcons.length === 0" class="empty-state">
              <el-icon :size="48" color="var(--color-text-tertiary)"><Search /></el-icon>
              <p>未找到匹配的图标</p>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <div class="selected-preview" v-if="tempSelected">
            <span>已选择：</span>
            <div class="preview-badge" :style="{ backgroundColor: color }">
              <el-icon :size="16">
                <component :is="getIconComponent(tempSelected)" />
              </el-icon>
            </div>
            <span class="preview-text">{{ tempSelected }}</span>
          </div>
          <div class="footer-actions">
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="confirmSelection">确定</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import * as allIcons from '@element-plus/icons-vue'
import { Edit, Search } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'Folder'
  },
  color: {
    type: String,
    default: 'var(--color-primary)'
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const searchKeyword = ref('')
const tempSelected = ref(props.modelValue)
const activeCategory = ref('all')

const iconCategories = [
  { key: 'all', label: '全部图标', icon: 'Grid' },
  { key: 'folder', label: '文件夹', icon: 'Folder' },
  { key: 'business', label: '商务办公', icon: 'Briefcase' },
  { key: 'tech', label: '技术开发', icon: 'Monitor' },
  { key: 'data', label: '数据分析', icon: 'DataAnalysis' },
  { key: 'user', label: '用户团队', icon: 'User' },
  { key: 'media', label: '媒体文件', icon: 'Film' },
  { key: 'tool', label: '工具设置', icon: 'Setting' },
  { key: 'symbol', label: '符号标志', icon: 'Star' }
]

const categoryIcons = {
  folder: [
    { name: 'Folder', label: '文件夹' },
    { name: 'FolderOpened', label: '打开文件夹' },
    { name: 'FolderAdd', label: '添加文件夹' },
    { name: 'FolderRemove', label: '删除文件夹' },
    { name: 'FolderChecked', label: '完成文件夹' },
    { name: 'Document', label: '文档' },
    { name: 'DocumentCopy', label: '复制文档' },
    { name: 'DocumentAdd', label: '添加文档' },
    { name: 'DocumentRemove', label: '删除文档' },
    { name: 'DocumentChecked', label: '完成文档' },
    { name: 'DocumentDelete', label: '删除文档' },
    { name: 'Files', label: '多文件' },
    { name: 'Collection', label: '收藏夹' },
    { name: 'CollectionTag', label: '标签收藏' },
    { name: 'Box', label: '盒子' },
    { name: 'Package', label: '包裹' }
  ],
  business: [
    { name: 'Briefcase', label: '公文包' },
    { name: 'Suitcase', label: '手提箱' },
    { name: 'Calendar', label: '日历' },
    { name: 'Date', label: '日期' },
    { name: 'Timer', label: '计时器' },
    { name: 'Clock', label: '时钟' },
    { name: 'AlarmClock', label: '闹钟' },
    { name: 'Schedule', label: '日程' },
    { name: 'Memo', label: '备忘录' },
    { name: 'Notebook', label: '笔记本' },
    { name: 'Reading', label: '阅读' },
    { name: 'Money', label: '金钱' },
    { name: 'Coin', label: '硬币' },
    { name: 'Wallet', label: '钱包' },
    { name: 'CreditCard', label: '信用卡' },
    { name: 'ShoppingCart', label: '购物车' },
    { name: 'Goods', label: '商品' },
    { name: 'Van', label: '货车' },
    { name: 'Present', label: '礼物' },
    { name: 'Trophy', label: '奖杯' },
    { name: 'Medal', label: '奖章' },
    { name: 'Flag', label: '旗帜' }
  ],
  tech: [
    { name: 'Monitor', label: '显示器' },
    { name: 'Desktop', label: '桌面' },
    { name: 'Cellphone', label: '手机' },
    { name: 'Iphone', label: 'iPhone' },
    { name: 'Platform', label: '平台' },
    { name: 'Connection', label: '连接' },
    { name: 'Link', label: '链接' },
    { name: 'Cpu', label: 'CPU' },
    { name: 'SetUp', label: '设置' },
    { name: 'Tools', label: '工具' },
    { name: 'MagicStick', label: '魔法棒' },
    { name: 'Key', label: '钥匙' },
    { name: 'Lock', label: '锁定' },
    { name: 'Unlock', label: '解锁' },
    { name: 'View', label: '查看' },
    { name: 'Hide', label: '隐藏' },
    { name: 'Camera', label: '相机' },
    { name: 'VideoCamera', label: '摄像机' },
    { name: 'Picture', label: '图片' },
    { name: 'Film', label: '电影' },
    { name: 'Headset', label: '耳机' },
    { name: 'Mic', label: '麦克风' },
    { name: 'Location', label: '定位' },
    { name: 'Position', label: '位置' },
    { name: 'Aim', label: '瞄准' }
  ],
  data: [
    { name: 'DataAnalysis', label: '数据分析' },
    { name: 'DataLine', label: '数据线' },
    { name: 'DataBoard', label: '数据板' },
    { name: 'PieChart', label: '饼图' },
    { name: 'Histogram', label: '柱状图' },
    { name: 'TrendCharts', label: '趋势图' },
    { name: 'Grid', label: '网格' },
    { name: 'List', label: '列表' },
    { name: 'Menu', label: '菜单' },
    { name: 'Operation', label: '操作' },
    { name: 'More', label: '更多' },
    { name: 'MoreFilled', label: '更多填充' },
    { name: 'Sort', label: '排序' },
    { name: 'Rank', label: '排名' },
    { name: 'FullScreen', label: '全屏' },
    { name: 'Expand', label: '展开' },
    { name: 'Fold', label: '折叠' }
  ],
  user: [
    { name: 'User', label: '用户' },
    { name: 'UserFilled', label: '用户填充' },
    { name: 'Avatar', label: '头像' },
    { name: 'Users', label: '多用户' },
    { name: 'Team', label: '团队' },
    { name: 'Message', label: '消息' },
    { name: 'ChatDotRound', label: '聊天气泡' },
    { name: 'ChatLineRound', label: '聊天线' },
    { name: 'ChatRound', label: '聊天圆' },
    { name: 'Bell', label: '铃铛' },
    { name: 'BellFilled', label: '铃铛填充' },
    { name: 'Service', label: '服务' },
    { name: 'Phone', label: '电话' },
    { name: 'PhoneFilled', label: '电话填充' },
    { name: 'Promotion', label: '推广' }
  ],
  media: [
    { name: 'Picture', label: '图片' },
    { name: 'PictureFilled', label: '图片填充' },
    { name: 'PictureRounded', label: '圆角图片' },
    { name: 'Camera', label: '相机' },
    { name: 'CameraFilled', label: '相机填充' },
    { name: 'VideoCamera', label: '摄像机' },
    { name: 'VideoCameraFilled', label: '摄像机填充' },
    { name: 'VideoPlay', label: '播放' },
    { name: 'VideoPause', label: '暂停' },
    { name: 'Film', label: '电影' },
    { name: 'Headset', label: '耳机' },
    { name: 'Mic', label: '麦克风' },
    { name: 'Mute', label: '静音' },
    { name: 'Volume', label: '音量' },
    { name: 'Upload', label: '上传' },
    { name: 'UploadFilled', label: '上传填充' },
    { name: 'Download', label: '下载' },
    { name: 'DownloadFilled', label: '下载填充' }
  ],
  tool: [
    { name: 'Setting', label: '设置' },
    { name: 'SettingFilled', label: '设置填充' },
    { name: 'SetUp', label: '配置' },
    { name: 'Tools', label: '工具' },
    { name: 'More', label: '更多' },
    { name: 'MoreFilled', label: '更多填充' },
    { name: 'Operation', label: '操作' },
    { name: 'Switch', label: '开关' },
    { name: 'TurnOff', label: '关闭' },
    { name: 'Open', label: '打开' },
    { name: 'Search', label: '搜索' },
    { name: 'ZoomIn', label: '放大' },
    { name: 'ZoomOut', label: '缩小' },
    { name: 'FullScreen', label: '全屏' },
    { name: 'Print', label: '打印' },
    { name: 'CopyDocument', label: '复制' },
    { name: 'Scissors', label: '剪切' },
    { name: 'Delete', label: '删除' },
    { name: 'DeleteFilled', label: '删除填充' },
    { name: 'Refresh', label: '刷新' },
    { name: 'RefreshLeft', label: '左刷新' },
    { name: 'RefreshRight', label: '右刷新' }
  ],
  symbol: [
    { name: 'Star', label: '星星' },
    { name: 'StarFilled', label: '星星填充' },
    { name: 'Check', label: '勾选' },
    { name: 'CircleCheck', label: '圆形勾选' },
    { name: 'CircleCheckFilled', label: '圆形勾选填充' },
    { name: 'Close', label: '关闭' },
    { name: 'CircleClose', label: '圆形关闭' },
    { name: 'CircleCloseFilled', label: '圆形关闭填充' },
    { name: 'Plus', label: '加号' },
    { name: 'CirclePlus', label: '圆形加号' },
    { name: 'CirclePlusFilled', label: '圆形加号填充' },
    { name: 'Minus', label: '减号' },
    { name: 'CircleMinus', label: '圆形减号' },
    { name: 'Select', label: '选择' },
    { name: 'SuccessFilled', label: '成功' },
    { name: 'WarningFilled', label: '警告' },
    { name: 'InfoFilled', label: '信息' },
    { name: 'QuestionFilled', label: '疑问' },
    { name: 'CircleWarningFilled', label: '警告圆' },
    { name: 'Sunny', label: '晴天' },
    { name: 'Moon', label: '月亮' },
    { name: 'Cloudy', label: '多云' },
    { name: 'Drizzling', label: '小雨' },
    { name: 'Lightning', label: '闪电' },
    { name: 'WindPower', label: '风力' }
  ]
}

const allIconsList = computed(() => {
  const list = []
  const addedNames = new Set()
  
  Object.values(categoryIcons).forEach(icons => {
    icons.forEach(icon => {
      if (!addedNames.has(icon.name) && allIcons[icon.name]) {
        addedNames.add(icon.name)
        list.push({
          ...icon,
          component: allIcons[icon.name]
        })
      }
    })
  })
  
  return list
})

const currentCategoryIcons = computed(() => {
  if (activeCategory.value === 'all') {
    return allIconsList.value
  }
  const icons = categoryIcons[activeCategory.value] || []
  return icons
    .filter(icon => allIcons[icon.name])
    .map(icon => ({
      ...icon,
      component: allIcons[icon.name]
    }))
})

const filteredIcons = computed(() => {
  const icons = currentCategoryIcons.value
  if (!searchKeyword.value) return icons
  
  const keyword = searchKeyword.value.toLowerCase()
  return icons.filter(icon => 
    icon.name.toLowerCase().includes(keyword) ||
    icon.label.toLowerCase().includes(keyword)
  )
})

const currentIcon = computed(() => {
  return allIcons[props.modelValue] || allIcons.Folder
})

const getIconComponent = (iconName) => {
  return allIcons[iconName] || allIcons.Folder
}

const selectIcon = (iconName) => {
  tempSelected.value = iconName
}

const openPicker = () => {
  tempSelected.value = props.modelValue
  searchKeyword.value = ''
  activeCategory.value = 'all'
  visible.value = true
}

const confirmSelection = () => {
  emit('update:modelValue', tempSelected.value)
  visible.value = false
}

watch(visible, (val) => {
  if (val) {
    tempSelected.value = props.modelValue
  }
})
</script>

<style scoped>
.icon-picker {
  display: inline-block;
}

.icon-preview-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
}

.icon-preview-wrapper:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(24, 24, 27, 0.15);
}

.icon-preview {
  width: 48px;
  height: 48px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.preview-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.preview-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.edit-icon {
  color: var(--color-text-tertiary);
  font-size: 16px;
}

.picker-container {
  display: flex;
  height: 450px;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  overflow: hidden;
}

.picker-sidebar {
  width: 140px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-primary);
  padding: 8px 0;
  overflow-y: auto;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.sidebar-item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.sidebar-item.active {
  background: var(--color-primary);
  color: white;
}

.picker-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-bar {
  padding: 12px;
  border-bottom: 1px solid var(--color-border-primary);
}

.icon-grid-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.icon-item:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-border-primary);
}

.icon-item.selected {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.icon-item-inner {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: transform 0.2s ease;
}

.icon-item:hover .icon-item-inner {
  transform: scale(1.1);
}

.icon-item-name {
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-tertiary);
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.preview-badge {
  width: 24px;
  height: 24px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.preview-text {
  font-weight: 500;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 600px) {
  .icon-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .picker-sidebar {
    width: 100px;
  }
  
  .sidebar-item {
    padding: 8px 12px;
    font-size: 12px;
  }
}
</style>
