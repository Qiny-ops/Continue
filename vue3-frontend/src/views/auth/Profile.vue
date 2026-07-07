<template>
  <div data-frontend-module-container="coding-frontend-account" class="account-container">
    <div>
      <div class="page-title"><span>个人账户</span></div>

      <div class="profile">
        <!-- 基本信息区 -->
        <div class="basic-info">
          <div class="avatar">
            <img
              v-if="userInfo.avatar"
              class="avatar-img"
              :src="userInfo.avatar"
              :alt="userInfo.name || '用户头像'"
            >
            <div v-else class="avatar-fallback">{{ (userInfo.name || userInfo.username || '用户').charAt(0) }}</div>
            <div class="avatar-edit" title="更换头像" @click="changeAvatar">
              <svg
                fill="currentColor"
                height="1em"
                width="1em"
                viewBox="0 0 16 16"
                class="icon"
                style="vertical-align: middle;"
              >
                <g>
                  <path
                    d="M14.5 13.25a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-13a.5.5 0 01-.5-.5v-1a.5.5 0 01.5-.5h13zM10.293 1.043a1 1 0 011.32-.083l.094.083 2.5 2.5a1 1 0 01.083 1.32l-.083.094-7 7a1 1 0 01-.576.284l-.131.009H4a1 1 0 01-.993-.883L3 11.25v-2.5a1 1 0 01.206-.608l.087-.1 7-7z"
                  />
                </g>
              </svg>
            </div>
          </div>

          <div class="identity">
            <div class="identity-row">
              <span>姓名：</span>
              <div class="username"><span>{{ userInfo.name || userInfo.username || '用户' }}</span></div>
            </div>
            <span class="role-badge" style="background-color: #fff;">
              {{ userInfo.systemRole || '普通用户' }}
            </span>
          </div>
        </div>

        <div class="content">
          <div class="content-title">账号信息</div>
          <div class="alert alert-info">
            <span class="alert-quote" />
            <svg
              fill="currentColor"
              height="1em"
              width="1em"
              viewBox="0 0 16 16"
              class="icon"
              style="vertical-align: middle;"
            >
              <g>
                <path
                  d="M8 16A8 8 0 108 0a8 8 0 000 16zm0-2A6 6 0 118 2a6 6 0 010 12zm0-8.2a1.15 1.15 0 100-2.3 1.15 1.15 0 000 2.3zm.5 6.7A.5.5 0 009 12V7a.5.5 0 00-.5-.5h-1A.5.5 0 017 7v5a.5.5 0 01.5.5h1z"
                />
              </g>
            </svg>
            <div class="alert-content">
              <span class="alert-msg">邮箱和密码可用于登录，以及作为代码托管 HTTPS 克隆、制品库认证、站内敏感操作等凭证。</span>
            </div>
          </div>
          <!-- 信息行 -->
          <div>
            <div class="info-item">
              <div class="info-label"><span>用户名：</span></div>
              <div class="info-cell">
                <div class="info-value username">
                  <div>{{ userInfo.username || '未设置' }}</div>
                </div>
              </div>
              <div class="info-actions">
                <a href="javascript:void(0)" @click="editUsername">编辑</a>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>邮箱：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <div class="value" :title="userInfo.email">{{ maskEmail(userInfo.email) || '未设置' }}</div>
                </div>
              </div>
              <div class="info-actions"><a href="javascript:void(0)" @click="editEmail">更改</a></div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>密码：</span></div>
              <div class="info-cell">
                <div class="info-value"><span>*********</span></div>
              </div>
              <div class="info-actions">
                <a href="javascript:void(0)" @click="changePassword">更改</a>
                <span class="divider">|</span>
                <a href="javascript:void(0)" @click="resetPassword">重置</a>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>手机：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <span class="label" :style="{ backgroundColor: userInfo.phone ? 'var(--color-success-light)' : 'rgb(250, 247, 212)' }">
                    {{ userInfo.phone || '未绑定' }}
                  </span>
                </div>
              </div>
              <div class="info-actions"><a href="javascript:void(0)" @click="phoneDialogVisible = true">{{ userInfo.phone ? '更改' : '绑定' }}</a></div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>职位：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <div>{{ userInfo.title || '未设置' }}</div>
                </div>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>状态：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <span class="label" :style="{ backgroundColor: userInfo.status === 'active' ? 'var(--color-success-light)' : 'var(--color-warning-light)', color: userInfo.status === 'active' ? 'var(--color-success)' : 'var(--color-warning)' }">
                    {{ userInfo.status === 'active' ? '正常' : userInfo.status === 'disabled' ? '已禁用' : '暂停' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>最后登录：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <div>{{ formatDateTime(userInfo.lastLoginTime) || '暂无记录' }}</div>
                </div>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label"><span>注册时间：</span></div>
              <div class="info-cell">
                <div class="info-value">
                  <div>{{ formatDateTime(userInfo.createdAt) || '暂无记录' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 手机绑定对话框 -->
      <el-dialog v-model="phoneDialogVisible" title="绑定手机" width="400px">
        <el-form ref="phoneFormRef" :model="phoneForm" :rules="phoneRules" label-width="100px">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="phoneForm.phone" placeholder="请输入手机号" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="phoneDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="savingPhone" @click="submitPhoneBinding">确认绑定</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 用户名编辑对话框 -->
      <el-dialog v-model="usernameDialogVisible" title="编辑用户名" width="400px">
        <el-form :model="usernameForm" :rules="usernameRules" label-width="100px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="usernameForm.username" placeholder="请输入新的用户名" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="usernameDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="savingUsername" @click="submitUsernameChange">确认修改</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 邮箱编辑对话框 -->
      <el-dialog v-model="emailDialogVisible" title="更改邮箱" width="400px">
        <el-form ref="emailFormRef" :model="emailForm" :rules="emailRules" label-width="100px">
          <el-form-item label="当前邮箱">
            <div class="current-email">{{ userInfo.email || '未设置' }}</div>
          </el-form-item>
          <el-form-item label="新邮箱" prop="email">
            <el-input v-model="emailForm.email" placeholder="请输入新的邮箱地址" />
          </el-form-item>
          <el-form-item label="验证码" prop="code">
            <div class="code-input">
              <el-input v-model="emailForm.code" placeholder="请输入验证码" />
              <el-button type="primary" :disabled="sendingEmailCode || !emailForm.email" @click="sendEmailCode">
                {{ sendingEmailCode ? `${emailCountdown}秒后重试` : '获取验证码' }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="emailDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="savingEmail" @click="submitEmailChange">确认修改</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 修改密码对话框（沿用原有） -->
      <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
        >
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input
              v-model="passwordForm.currentPassword"
              type="password"
              show-password
              placeholder="请输入当前密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              show-password
              placeholder="请输入新密码"
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入新密码"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="passwordDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="changingPassword" @click="submitPasswordChange">确认修改</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/modules/user'
import { getAvatarUrl } from '@/utils/avatar'

import authApi from '@/api/modules/auth'

const userStore = useUserStore()

// 响应式数据
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const phoneDialogVisible = ref(false)
const savingPhone = ref(false)
const usernameDialogVisible = ref(false)
const savingUsername = ref(false)
const emailDialogVisible = ref(false)
const savingEmail = ref(false)
const sendingEmailCode = ref(false)
const emailCountdown = ref(0)
const phoneForm = reactive({
  phone: ''
})
const usernameForm = reactive({
  username: ''
})
const emailForm = reactive({
  email: '',
  code: ''
})

const phoneRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const usernameRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ]
}

const emailRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

const phoneFormRef = ref()

const submitPhoneBinding = async () => {
  try {
    await phoneFormRef.value.validate()
    savingPhone.value = true
    const res = await userStore.updateUserInfo({ phone: phoneForm.phone })
    if (res) {
      userInfo.phone = phoneForm.phone
      phoneDialogVisible.value = false
      ElMessage.success('手机绑定成功')
    }
  } catch (error) {
    if (error !== false) {
      ElMessage.error(`手机绑定失败: ${  error.message}`)
    }
  } finally {
    savingPhone.value = false
  }
}

// 用户信息（从API获取并映射显示）
const userInfo = reactive({
  id: '',
  username: '',
  name: '',
  email: '',
  phone: '',
  avatar: '',
  title: '',
  systemRole: '',
  status: 'active',
  lastLoginTime: '',
  lastLoginIp: '',
  createdAt: ''
})

// 编辑表单
const editForm = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  title: ''
})

// 密码修改表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码表单引用
const passwordFormRef = ref()
// 邮箱表单引用
const emailFormRef = ref()

// 密码验证规则
const passwordRules = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}



// 邮箱脱敏
const maskEmail = (email) => {
  if (!email) return ''
  const [name, domain] = email.split('@')
  if (!domain) return email
  const masked = name.length <= 4 ? `${name.slice(0, 2)  }****` : `${name.slice(0, 4)  }****`
  return `${masked}@${domain}`
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return dateStr
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch {
    return dateStr
  }
}

// 将 store 用户数据映射到本页展示模型
const mapUserToView = (u) => {
  userInfo.id = u?.id || ''
  userInfo.username = u?.username || ''
  userInfo.name = u?.name || u?.username || ''
  userInfo.email = u?.email || ''
  userInfo.phone = u?.phone || ''
  userInfo.title = u?.title || ''
  userInfo.systemRole = u?.system_role || ''
  userInfo.status = u?.status || 'active'
  userInfo.lastLoginTime = u?.last_login_time || ''
  userInfo.lastLoginIp = u?.last_login_ip || ''
  userInfo.createdAt = u?.created_at || ''
  userInfo.avatar = getAvatarUrl(u?.avatar)
}

// 初始化编辑表单
const initEditForm = () => {
  editForm.username = userInfo.username
  editForm.name = userInfo.name
  editForm.email = userInfo.email
  editForm.phone = userInfo.phone
  editForm.title = userInfo.title
}





// 更换头像
const changeAvatar = async () => {
  try {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async (e) => {
      const file = e.target.files[0]
      if (file) {
        try {
          const res = await authApi.uploadAvatar(file)
          if (res.code === 200) {
            userInfo.avatar = getAvatarUrl(res.data.avatar)
            ElMessage.success('头像上传成功')
          } else {
            throw new Error(res.message)
          }
        } catch (error) {
          ElMessage.error(`头像上传失败: ${  error.message}`)
        }
      }
    }
    input.click()
  } catch (error) {
    ElMessage.error(`头像上传失败: ${  error.message}`)
  }
}

// 修改密码
const changePassword = () => {
  passwordDialogVisible.value = true
  Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
}

// 提交密码修改
const submitPasswordChange = async () => {
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    const res = await authApi.changePassword({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })
    if (res.code === 200) {
      ElMessage.success('密码修改成功')
      passwordDialogVisible.value = false
    } else {
      throw new Error(res.message)
    }
  } catch (error) {
    if (error !== false) ElMessage.error(`密码修改失败: ${  error.message || '请重试' }`)
  } finally {
    changingPassword.value = false
  }
}

// 编辑用户名
const editUsername = () => {
  usernameForm.username = userInfo.username
  usernameDialogVisible.value = true
}

// 提交用户名修改
const submitUsernameChange = async () => {
  try {
    savingUsername.value = true
    const res = await userStore.updateUserInfo({ username: usernameForm.username })
    if (res) {
      userInfo.username = usernameForm.username
      usernameDialogVisible.value = false
      ElMessage.success('用户名修改成功')
    }
  } catch (error) {
    ElMessage.error(`用户名修改失败: ${  error.message}`)
  } finally {
    savingUsername.value = false
  }
}

// 编辑邮箱
const editEmail = () => {
  emailForm.email = ''
  emailForm.code = ''
  emailDialogVisible.value = true
}

// 发送邮箱验证码
const sendEmailCode = async () => {
  try {
    sendingEmailCode.value = true
    emailCountdown.value = 60
    const res = await authApi.sendEmailCode({ email: emailForm.email })
    if (res.code === 200) {
      ElMessage.success('验证码已发送到新邮箱')
      const timer = setInterval(() => {
        emailCountdown.value--
        if (emailCountdown.value <= 0) {
          clearInterval(timer)
          sendingEmailCode.value = false
        }
      }, 1000)
    } else {
      sendingEmailCode.value = false
      throw new Error(res.message)
    }
  } catch (error) {
    sendingEmailCode.value = false
    ElMessage.error(`验证码发送失败: ${  error.message}`)
  }
}

// 提交邮箱修改
const submitEmailChange = async () => {
  try {
    await emailFormRef.value.validate()
    savingEmail.value = true
    const res = await authApi.updateEmail({
      email: emailForm.email,
      code: emailForm.code
    })
    if (res.code === 200) {
      userInfo.email = emailForm.email
      emailDialogVisible.value = false
      ElMessage.success('邮箱修改成功')
    } else {
      throw new Error(res.message)
    }
  } catch (error) {
    if (error !== false) {
      ElMessage.error(`邮箱修改失败: ${  error.message}`)
    }
  } finally {
    savingEmail.value = false
  }
}

// 重置密码
const resetPassword = async () => {
  try {
    await ElMessageBox.confirm(
      '重置密码后，系统将向您的邮箱发送一封包含新密码的邮件。确认重置吗？',
      '确认重置密码',
      {
        confirmButtonText: '确认重置',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await authApi.resetPassword()
    ElMessage.success('密码重置邮件已发送，请查收您的邮箱')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('密码重置失败，请重试')
    }
  }
}

// 从后端加载个人信息
const loadProfile = async () => {
  const u = await userStore.fetchUserInfo()
  mapUserToView(u)
  initEditForm()
}

// 组件挂载时初始化
onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
/* 页面主容器外层容器（由内联 style 改为类） */
.account-container {
  height: 100%;
  overflow: auto;
  background: #fff;
}

/* 顶部标题 */
.page-title {
  padding: 30px 30px 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary);
  font-family: PingFangSC-Medium
}

/* 页面主容器 */
.profile {
  padding: 30px;
  background: #fff
}

/* 基本信息区 */
.basic-info {
  display: flex;
  margin-bottom: 30px;
}

/* 头像 */
.avatar {
  position: relative;
  width: 128px;
  height: 128px;
}

.avatar-img, .avatar-fallback {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border-primary);
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 48px;
  font-weight: bold;
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 36px;
  height: 36px;
  background: #fff;
  border: 1px solid var(--color-border-primary);
  border-radius: 50%;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* 名称与身份 */
.identity {
  flex: 1 1;
  padding: 24px 30px 0;
}

.identity-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.username span {
  color: var(--color-text-secondary);
  font-size: 16px;
  font-weight: 500;
  height: 24px;
}

.role-badge {
  display: inline-block;
  padding: 0px 12px;
  border-radius: 2px;
  font-size: 12px;
  border: 1px solid var(--color-success);
  color: var(--color-success);
}

/* 信息卡片 */
.content {
  width: 100%;
}

.content-title {
  display: flex;
  align-items: baseline;
  margin-bottom: 14px
}

/* 提示条 */
.alert {
  width: 900px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 14px 0 20px;
  padding: 12px 14px;
  border-radius: 2px;
  border: 1px solid transparent;
}

.alert-info {
  position: relative;
  display: flex;
  padding: 10px 8px 10px 5px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  border: 1px solid var(--color-border-primary);
  border-left-width: 0;
  border-radius: 2px;
  transition: all .25s;
  font-feature-settings: "tnum";
  background: var(--color-primary-light);
  border-color: var(--color-primary-light);
  color: var(--color-primary);
}

.alert-info::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-primary);
}

.alert-warning {
  position: relative;
  display: flex;
  padding: 10px 8px 10px 5px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  border: 1px solid var(--color-border-primary);
  border-left-width: 0;
  border-radius: 2px;
  transition: all .25s;
  font-feature-settings: "tnum";
  background: var(--color-warning-light);
  border-color: var(--color-warning-light);
  color: var(--color-warning);
}

.alert-warning::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-warning);
}

.icon {
  flex: none;
}

.alert-content .alert-msg {
  font-size: 13px;
}

/* 信息行 */
.info-item {
  display: flex;
  width: 600px;
  margin-bottom: 20px
}

.info-label {
  flex: 0 0 14%;
  max-width: 14%;
  flex-grow: 0;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.info-cell {
  flex: 1 1;
  max-width: 42%
}

.info-value {
  color: var(--color-text-primary);
  font-size: 16px;
  height: 21px;
}

.info-actions {
  width: 120px;
  text-align: right;
}

.info-actions a,
.link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: none;
}

.value {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.label {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
}

.divider {
  margin: 0 8px;
  color: var(--color-text-tertiary);
}

.code-input {
  display: flex;
  gap: 10px;
}

.code-input .el-input {
  flex: 1;
}

.current-email {
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* 退出团队块 */
.team-exit {
  margin-top: 42px;
}

.section-title {
  margin-bottom: 14px;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 500;
}

.section-actions {
  font-size: 16px;
}

.button {
  border: none;
  border-radius: 2px;
  padding: 8px 22px;
  cursor: pointer;
}

.button-danger {
  background: var(--color-danger);
  color: #fff;
}

.button-danger:hover {
  background: var(--color-danger);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .basic-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .info-actions {
    width: auto;
    margin-left: 12px;
  }
}
</style>
