<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="caseData ? '编辑测试用例' : '新建测试用例'"
    width="700px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="用例名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="优先级" prop="priority">
            <el-select v-model="form.priority" placeholder="选择优先级">
              <el-option label="P0 - 最高" value="p0" />
              <el-option label="P1 - 高" value="p1" />
              <el-option label="P2 - 中" value="p2" />
              <el-option label="P3 - 低" value="p3" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-select v-model="form.status" placeholder="选择状态">
              <el-option label="草稿" value="draft" />
              <el-option label="就绪" value="ready" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="前置条件" prop="precondition">
        <el-input
          v-model="form.precondition"
          type="textarea"
          :rows="3"
          placeholder="如: 用户已登录、数据已准备"
        />
      </el-form-item>

      <el-form-item label="测试点" prop="testpoint">
        <el-input
          v-model="form.testpoint"
          type="textarea"
          :rows="3"
          placeholder="具体测试内容描述"
        />
      </el-form-item>

      <el-form-item label="预期结果" prop="expectation">
        <el-input
          v-model="form.expectation"
          type="textarea"
          :rows="3"
          placeholder="如: HTTP状态码200，返回code为0"
        />
      </el-form-item>

      <el-form-item label="测试数据" prop="test_data">
        <el-input
          v-model="testDataStr"
          type="textarea"
          :rows="5"
          placeholder='测试数据 (JSON格式)，如: {"username": "admin", "password": "123456"}'
        />
      </el-form-item>

      <el-form-item label="标签" prop="tags">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入标签"
        />
      </el-form-item>

      <el-form-item label="知识库ID" prop="knowledge_base_id">
        <el-input v-model="form.knowledge_base_id" placeholder="关联的知识库ID（可选）" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  caseData: Object,
  projectId: [String, Number]
})

const emit = defineEmits(['update:modelValue', 'save'])

const formRef = ref(null)

const form = ref({
  name: '',
  priority: 'p2',
  status: 'draft',
  precondition: '',
  testpoint: '',
  expectation: '',
  test_data: {},
  tags: [],
  knowledge_base_id: ''
})

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  testpoint: [{ required: true, message: '请输入测试点', trigger: 'blur' }],
  expectation: [{ required: true, message: '请输入预期结果', trigger: 'blur' }]
}

const testDataStr = computed({
  get: () => {
    try {
      return JSON.stringify(form.value.test_data, null, 2)
    } catch {
      return '{}'
    }
  },
  set: (val) => {
    try {
      form.value.test_data = JSON.parse(val)
    } catch {
      // keep previous value on parse error
    }
  }
})

watch(() => props.modelValue, (visible) => {
  if (visible) {
    if (props.caseData) {
      form.value = {
        name: props.caseData.name || '',
        priority: props.caseData.priority || 'p2',
        status: props.caseData.status || 'draft',
        precondition: props.caseData.precondition || '',
        testpoint: props.caseData.testpoint || '',
        expectation: props.caseData.expectation || '',
        test_data: props.caseData.test_data || {},
        tags: props.caseData.tags || [],
        knowledge_base_id: props.caseData.knowledge_base_id || ''
      }
    } else {
      form.value = {
        name: '',
        priority: 'p2',
        status: 'draft',
        precondition: '',
        testpoint: '',
        expectation: '',
        test_data: {},
        tags: [],
        knowledge_base_id: ''
      }
    }
  }
})

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    emit('save', {
      ...form.value,
      id: props.caseData?.id
    })
  } catch {
    ElMessage.warning('请完善表单信息')
  }
}
</script>
