<template>
  <div class="webtest-page">
    <div class="page-header">
      <h1>Web自动化测试用例</h1>
      <el-button type="primary" @click="runAllTests" :loading="runningAll">
        批量执行
      </el-button>
    </div>

    <div class="test-list">
      <el-table :data="testCases" style="width: 100%" v-loading="executing">
        <el-table-column type="index" width="50" label="#" />
        <el-table-column prop="name" label="用例名称" min-width="200" />
        <el-table-column prop="target" label="目标系统" width="150" />
        <el-table-column prop="steps" label="测试步骤" min-width="300">
          <template #default="{ row }">
            <div class="steps-preview">{{ row.steps }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="info">待执行</el-tag>
            <el-tag v-else-if="row.status === 'running'" type="warning">执行中</el-tag>
            <el-tag v-else-if="row.status === 'success'" type="success">通过</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="runSingleTest(row)" :loading="row.status === 'running'">
              执行
            </el-button>
            <el-button size="small" @click="viewResult(row)" :disabled="!row.result">
              结果
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 执行结果弹窗 -->
    <el-dialog v-model="resultDialogVisible" :title="currentCase?.name" width="80%" top="5vh">
      <div class="result-content">
        <div class="result-header">
          <span>执行状态：</span>
          <el-tag :type="currentCase?.status === 'success' ? 'success' : 'danger'">
            {{ currentCase?.status === 'success' ? '通过' : '失败' }}
          </el-tag>
        </div>

        <!-- 执行步骤 -->
        <div v-if="currentCase?.result?.steps?.length" class="steps-result">
          <h4>执行步骤</h4>
          <el-timeline>
            <el-timeline-item
              v-for="step in currentCase.result.steps"
              :key="step.seq"
              :type="step.success ? 'success' : 'danger'"
            >
              <div class="step-content">
                <div class="step-header">
                  <span class="step-title">{{ step.seq }}. {{ step.description || step.action }}</span>
                  <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                    {{ step.success ? '成功' : '失败' }}
                  </el-tag>
                </div>
                <div v-if="step.error" class="step-error">{{ step.error }}</div>
                <div v-if="step.screenshot" class="step-screenshot">
                  <el-image
                    :src="'data:image/jpeg;base64,' + step.screenshot"
                    :preview-src-list="['data:image/jpeg;base64,' + step.screenshot]"
                    fit="contain"
                    style="max-width: 100%; max-height: 300px"
                  />
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 断言结果 -->
        <div v-if="currentCase?.result?.assertions?.length" class="assertions-result">
          <h4>断言验证</h4>
          <div
            v-for="(assertion, index) in currentCase.result.assertions"
            :key="index"
            class="assertion-item"
            :class="{ 'assertion-pass': assertion.success, 'assertion-fail': !assertion.success }"
          >
            <span class="assertion-icon">{{ assertion.success ? '✓' : '✗' }}</span>
            <span class="assertion-desc">{{ assertion.description }}</span>
            <el-tag :type="assertion.success ? 'success' : 'danger'" size="small">
              {{ assertion.success ? '通过' : '失败' }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import webAutoApi from '@/api/modules/webauto.js'

const FRONTEND_BASE_URL = import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173'
const API_TESTING_BASE_URL = import.meta.env.VITE_API_TESTING_URL || 'http://localhost:8002/api/v1'
const getFrontendUrl = (path) => `${FRONTEND_BASE_URL}${path}`

// 测试用例列表
const testCases = ref([
  {
    id: 1,
    name: '用户登录验证',
    target: '本地系统',
    base_url: getFrontendUrl('/login'),
    precondition: '无',
    steps: '1. 输入用户名admin\n2. 输入密码admin123\n3. 点击登录按钮',
    expected_result: '登录成功，跳转到项目列表页面',
    status: 'pending',
    result: null
  },
  {
    id: 2,
    name: '项目列表查看',
    target: '本地系统',
    base_url: getFrontendUrl('/projects'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 查看项目列表\n2. 点击第一个项目进入详情',
    expected_result: '成功进入项目详情页面',
    status: 'pending',
    result: null
  },
  {
    id: 3,
    name: '测试用例创建',
    target: '本地系统',
    base_url: getFrontendUrl('/testcases'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 点击新建测试用例\n2. 填写用例名称"登录验证测试"\n3. 填写用例描述\n4. 点击保存',
    expected_result: '测试用例创建成功',
    status: 'pending',
    result: null
  },
  {
    id: 4,
    name: '搜索功能验证',
    target: '本地系统',
    base_url: getFrontendUrl('/projects'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 在搜索框输入项目名称\n2. 点击搜索按钮\n3. 验证搜索结果',
    expected_result: '搜索结果正确显示',
    status: 'pending',
    result: null
  },
  {
    id: 5,
    name: '用户个人设置',
    target: '本地系统',
    base_url: getFrontendUrl('/profile'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 进入个人设置页面\n2. 修改昵称\n3. 点击保存\n4. 验证修改成功',
    expected_result: '个人设置保存成功',
    status: 'pending',
    result: null
  },
  {
    id: 6,
    name: '项目成员管理',
    target: '本地系统',
    base_url: getFrontendUrl('/projects/1/members'),
    precondition: '已登录且有项目权限',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 点击添加成员\n2. 输入成员邮箱\n3. 选择角色\n4. 点击确认添加',
    expected_result: '成员添加成功',
    status: 'pending',
    result: null
  },
  {
    id: 7,
    name: 'API测试用例创建',
    target: '本地系统',
    base_url: getFrontendUrl('/apitest'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 点击新建API测试\n2. 输入接口地址\n3. 选择请求方法\n4. 添加请求参数\n5. 点击保存',
    expected_result: 'API测试用例创建成功',
    status: 'pending',
    result: null
  },
  {
    id: 8,
    name: '知识库文档上传',
    target: '本地系统',
    base_url: getFrontendUrl('/knowledge'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 点击上传文档\n2. 选择文件\n3. 点击确认上传\n4. 等待上传完成',
    expected_result: '文档上传成功',
    status: 'pending',
    result: null
  },
  {
    id: 9,
    name: '测试报告查看',
    target: '本地系统',
    base_url: getFrontendUrl('/reports'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 进入测试报告列表\n2. 点击查看报告详情\n3. 验证报告内容',
    expected_result: '测试报告正确显示',
    status: 'pending',
    result: null
  },
  {
    id: 10,
    name: '用户退出登录',
    target: '本地系统',
    base_url: getFrontendUrl('/dashboard'),
    precondition: '已登录',
    login_url: getFrontendUrl('/login'),
    username: 'admin',
    password: 'admin123',
    steps: '1. 点击用户头像\n2. 点击退出登录\n3. 确认退出',
    expected_result: '成功退出登录，跳转到登录页',
    status: 'pending',
    result: null
  }
])

const executing = ref(false)
const runningAll = ref(false)
const resultDialogVisible = ref(false)
const currentCase = ref(null)

// 执行单个测试（对接 Web 自动化微服务：前端 → Django /webauto/execute/ → web-automation-service:8003）
// 说明：原先该页面把请求打到了 api-testing-service(:8002)/api/v1/execute，而该端点根本不存在（404），
// 导致每次点击「执行」都直接失败。现已改为走真正的 Web 自动化微服务。
const runSingleTest = async (testCase) => {
  testCase.status = 'running'
  executing.value = true

  const steps = []
  const assertions = []

  try {
    await new Promise((resolve, reject) => {
      webAutoApi.executeCaseStream(
        {
          // 内联用例：复用 precondition / steps / expected_result
          testcase: {
            precondition: testCase.precondition || '',
            steps: testCase.steps || '',
            expected_result: testCase.expected_result || ''
          },
          // 起始 URL（用例里的 base_url 即目标站点地址）
          start_url: testCase.base_url || '',
          site_hint: testCase.siteHint || ''
        },
        (event) => {
          const type = event?.type
          const data = event?.data || {}
          if (type === 'step') {
            const a = data.action || {}
            steps.push({
              seq: steps.length + 1,
              description: a.action || a.description || '',
              action: a.action || '',
              success: !!data.success,
              error: data.error || '',
              screenshot: data.screenshot || ''
            })
          } else if (type === 'report') {
            // 微服务给出最终判定
            testCase.status = data.passed ? 'success' : 'failed'
          } else if (type === 'error') {
            testCase.status = 'failed'
            steps.push({
              seq: steps.length + 1,
              description: '执行失败',
              action: '',
              success: false,
              error: data.message || '发生错误',
              screenshot: ''
            })
          }
        },
        (error) => reject(error),
        () => resolve()
      )
    })
    testCase.result = { steps, assertions }
  } catch (error) {
    ElMessage.error('执行失败: ' + (error?.message || '未知错误'))
    testCase.status = 'failed'
    testCase.result = { steps, assertions }
  } finally {
    executing.value = false
  }
}

// 批量执行
const runAllTests = async () => {
  runningAll.value = true
  for (const testCase of testCases.value) {
    if (testCase.status !== 'running') {
      await runSingleTest(testCase)
    }
  }
  runningAll.value = false
  ElMessage.success('批量执行完成')
}

// 查看结果
const viewResult = (testCase) => {
  currentCase.value = testCase
  resultDialogVisible.value = true
}
</script>

<style scoped>
.webtest-page {
  padding: 24px;
  background: var(--color-bg-secondary);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.test-list {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.steps-preview {
  white-space: pre-line;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.result-content {
  max-height: 70vh;
  overflow-y: auto;
}

.result-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.steps-result h4,
.assertions-result h4 {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
  color: var(--color-text-primary);
}

.step-content {
  margin-bottom: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
}

.step-error {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
  border-radius: 4px;
  font-size: 13px;
}

.step-screenshot {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
}

.assertions-result {
  margin-top: 20px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  font-size: 13px;
}

.assertion-item.assertion-pass {
  background: rgba(82, 196, 26, 0.1);
}

.assertion-item.assertion-fail {
  background: rgba(255, 77, 79, 0.1);
}

.assertion-icon {
  font-size: 16px;
  font-weight: bold;
}

.assertion-pass .assertion-icon {
  color: #52c41a;
}

.assertion-fail .assertion-icon {
  color: #ff4d4f;
}

.assertion-desc {
  flex: 1;
  color: var(--color-text-primary);
}
</style>
