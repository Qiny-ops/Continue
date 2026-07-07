<template>
  <div class="interface-tester">
    <div class="tester-layout">
      <div class="collection-wrapper" :style="{ width: panelCollapsed ? '0px' : panelWidth + 'px' }">
        <div
          class="collection-panel"
          :class="{ collapsed: panelCollapsed }"
        >
          <div v-show="!panelCollapsed" class="panel-resize-handle" @mousedown="startResize"></div>
          <div v-show="!panelCollapsed" class="panel-header">
            <div class="header-title clickable" @click="showAllCases">
              <el-icon class="title-icon"><Collection /></el-icon>
              <span>接口集合</span>
            </div>
            <div class="header-actions">
              <el-tooltip content="新建文件夹" placement="bottom">
                <el-button circle size="small" @click="handleAddFolder">
                  <el-icon><FolderAdd /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="新建请求" placement="bottom">
                <el-button circle size="small" @click="handleAddRequest">
                  <el-icon><Plus /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>

          <div v-show="!panelCollapsed" class="panel-search">
            <el-input
              v-model="sidebarSearch"
              placeholder="搜索接口..."
              clearable
              size="small"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div v-show="!panelCollapsed" class="collection-tree">
            <el-tree
              ref="treeRef"
              :data="filteredCollectionTree"
              :props="treeProps"
              default-expand-all
              highlight-current
              :expand-on-click-node="false"
              @node-click="handleNodeClick"
            >
              <template #default="{ node, data }">
                <div class="tree-node">
                  <div class="node-left">
                    <template v-if="data.method">
                      <span class="method-indicator" :class="data.method.toLowerCase()">{{ data.method }}</span>
                    </template>
                    <template v-else-if="data.type === 'folder'">
                      <el-icon class="folder-icon"><Folder /></el-icon>
                    </template>
                    <span class="node-label">{{ node.label }}</span>
                    <el-tag v-if="data.type === 'request' && data.testCases?.length" size="small" type="warning" class="case-badge">
                      {{ data.testCases.length }}用例
                    </el-tag>
                  </div>
                  <div class="node-actions">
                    <el-dropdown trigger="click" @command="(cmd) => handleNodeCommand(cmd, data)">
                      <el-button link size="small" class="action-btn">
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item v-if="data.type === 'folder'" command="addRequest">
                            <el-icon><Plus /></el-icon>添加请求
                          </el-dropdown-item>
                          <el-dropdown-item v-if="data.type === 'folder'" command="addFolder">
                            <el-icon><FolderAdd /></el-icon>添加文件夹
                          </el-dropdown-item>
                          <el-dropdown-item v-if="data.type === 'request'" command="addTestCase">
                            <el-icon><Document /></el-icon>添加测试用例
                          </el-dropdown-item>
                          <el-dropdown-item command="edit">
                            <el-icon><Edit /></el-icon>编辑
                          </el-dropdown-item>
                          <el-dropdown-item command="duplicate">
                            <el-icon><CopyDocument /></el-icon>复制
                          </el-dropdown-item>
                          <el-dropdown-item command="delete" divided>
                            <el-icon><Delete /></el-icon>删除
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </template>
            </el-tree>
          </div>
        </div>
      </div>
      <div
        class="sidebar-toggle"
        :style="{ left: (panelCollapsed ? 0 : panelWidth) + 'px' }"
        @click="panelCollapsed = !panelCollapsed"
      >
        <el-icon>
          <ArrowLeft v-if="!panelCollapsed" />
          <ArrowRight v-else />
        </el-icon>
      </div>

      <div class="case-list-panel">
        <div class="case-list-header">
          <h2 class="panel-title">
            <template v-if="viewMode === 'single' && selectedRequest">
              <span class="method-tag" :class="selectedRequest.method.toLowerCase()">{{ selectedRequest.method }}</span>
              {{ selectedRequest.name }}
            </template>
            <template v-else>
              <el-icon class="title-icon"><Collection /></el-icon>
              全部测试用例
              <span v-if="allTestCases.length > 0" class="title-count">{{ allTestCases.length }}</span>
            </template>
          </h2>
          <div class="panel-actions">
            <div class="batch-operation-wrapper">
              <el-button
                :class="{ 'batch-active': batchMode }"
                @click="toggleBatchMode"
              >
                <el-icon><Operation /></el-icon>
                {{ batchMode ? '取消操作' : '批量操作' }}
              </el-button>
              <Transition name="menu-fade">
                <div v-if="batchMode" class="batch-menu">
                  <div
                    class="batch-menu-item"
                    :class="{ disabled: selectedCaseIds.length === 0 }"
                    @click="handleBatchAction('execute')"
                  >
                    <el-icon><VideoPlay /></el-icon>
                    <span>批量执行</span>
                  </div>
                  <div
                    class="batch-menu-item"
                    :class="{ disabled: selectedCaseIds.length === 0 }"
                    @click="handleBatchAction('copy')"
                  >
                    <el-icon><CopyDocument /></el-icon>
                    <span>批量复制</span>
                  </div>
                  <div class="batch-menu-divider"></div>
                  <div
                    class="batch-menu-item danger"
                    :class="{ disabled: selectedCaseIds.length === 0 }"
                    @click="handleBatchAction('delete')"
                  >
                    <el-icon><Delete /></el-icon>
                    <span>批量删除</span>
                  </div>
                </div>
              </Transition>
            </div>
            <el-button @click="runSelectedRequestCases" :disabled="!selectedRequest?.testCases?.length" v-if="viewMode === 'single' && selectedRequest">
              <el-icon><VideoPlay /></el-icon>
              运行全部
            </el-button>
            <el-button type="primary" @click="openAddTestCase(selectedRequest)" v-if="viewMode === 'single' && selectedRequest">
              <el-icon><Plus /></el-icon>
              添加用例
            </el-button>
          </div>
        </div>

        <div class="batch-info" v-if="batchMode">
          <span class="batch-hint">
            <el-icon><InfoFilled /></el-icon>
            已选择 <strong>{{ selectedCaseIds.length }}</strong> 项
          </span>
        </div>

        <div class="case-list-content">
          <template v-if="viewMode === 'single' && selectedRequest">
            <div class="selected-request-info">
              <div class="info-row">
                <span class="info-label">请求地址</span>
                <span class="info-value url">{{ selectedRequest.url || '未设置' }}</span>
              </div>
            </div>

            <div class="cases-table-wrapper">
              <el-table
                ref="singleCasesTableRef"
                :data="selectedRequest.testCases || []"
                style="width: 100%"
                table-layout="fixed"
                empty-text="暂无测试用例"
                @selection-change="handleCaseSelectionChange"
              >
                <el-table-column v-if="batchMode" type="selection" width="50" />
                <el-table-column prop="name" label="用例名称" min-width="140">
                  <template #default="{ row }">
                    <div class="case-name-cell">
                      <el-icon v-if="row.lastResult === 'passed'" color="var(--color-success)"><CircleCheck /></el-icon>
                      <el-icon v-else-if="row.lastResult === 'failed'" color="var(--color-danger)"><CircleClose /></el-icon>
                      <span class="case-name-text">{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="request" label="请求参数" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="params-text">{{ formatRequestParams(row.request) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="lastResponse" label="响应结果" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="response-text" v-if="row.lastResponse">
                      <el-tag size="small" :type="row.lastResponse.status < 400 ? 'success' : 'danger'" class="status-tag">
                        {{ row.lastResponse.status }}
                      </el-tag>
                      <span class="response-body">{{ truncateText(row.lastResponse.body, 30) }}</span>
                    </span>
                    <span class="no-data-text" v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="assertions" label="断言" width="70" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" type="warning">{{ row.assertions?.length || 0 }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="lastResult" label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.lastResult === 'passed'" type="success" size="small">通过</el-tag>
                    <el-tag v-else-if="row.lastResult === 'failed'" type="danger" size="small">失败</el-tag>
                    <el-tag v-else type="info" size="small">未运行</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" align="center">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="openTestCase(selectedRequest, row)">
                      <el-icon><VideoPlay /></el-icon>运行
                    </el-button>
                    <el-button link size="small" @click="editTestCase(row)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button link type="danger" size="small" @click="deleteTestCase(row)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>

          <template v-else-if="viewMode === 'all'">
            <div class="cases-table-wrapper" v-if="allTestCases.length > 0">
              <el-table
                ref="allCasesTableRef"
                :data="allTestCases"
                style="width: 100%"
                table-layout="fixed"
                @selection-change="handleCaseSelectionChange"
              >
                <el-table-column v-if="batchMode" type="selection" width="50" />
                <el-table-column prop="requestName" label="所属接口" min-width="140">
                  <template #default="{ row }">
                    <div class="request-cell">
                      <span class="method-tag" :class="row.method.toLowerCase()">{{ row.method }}</span>
                      <span class="request-name-text">{{ row.requestName }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="caseName" label="用例名称" min-width="120">
                  <template #default="{ row }">
                    <div class="case-name-cell">
                      <el-icon v-if="row.lastResult === 'passed'" color="var(--color-success)"><CircleCheck /></el-icon>
                      <el-icon v-else-if="row.lastResult === 'failed'" color="var(--color-danger)"><CircleClose /></el-icon>
                      <span class="case-name-text">{{ row.caseName }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="request" label="请求参数" min-width="140" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="params-text">{{ formatRequestParams(row.request) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="lastResponse" label="响应结果" min-width="140" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="response-text" v-if="row.lastResponse">
                      <el-tag size="small" :type="row.lastResponse.status < 400 ? 'success' : 'danger'" class="status-tag">
                        {{ row.lastResponse.status }}
                      </el-tag>
                      <span class="response-body">{{ truncateText(row.lastResponse.body, 30) }}</span>
                    </span>
                    <span class="no-data-text" v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="assertionCount" label="断言" width="60" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" type="warning">{{ row.assertionCount }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="lastResult" label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.lastResult === 'passed'" type="success" size="small">通过</el-tag>
                    <el-tag v-else-if="row.lastResult === 'failed'" type="danger" size="small">失败</el-tag>
                    <el-tag v-else type="info" size="small">未运行</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" align="center">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="runSingleCase(row)">
                      <el-icon><VideoPlay /></el-icon>运行
                    </el-button>
                    <el-button link size="small" @click="editCaseFromManager(row)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button link type="danger" size="small" @click="deleteCaseFromManager(row)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="no-cases" v-else>
              <el-icon :size="48"><Document /></el-icon>
              <p>暂无测试用例</p>
              <el-button type="primary" @click="handleAddRequest">
                <el-icon><Plus /></el-icon>
                新建请求
              </el-button>
            </div>
          </template>

          <template v-else>
            <div class="select-hint">
              <el-icon :size="64"><Collection /></el-icon>
              <h3>选择接口查看测试用例</h3>
              <p>点击左侧"接口集合"查看所有用例，或选择具体接口</p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="editorDialogVisible"
      :title="selectedRequest?.name"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      class="editor-dialog"
      @close="handleEditorClose"
    >
      <template #header>
        <div class="dialog-header">
          <div class="dialog-title">
            <span class="method-badge" :class="requestForm.method.toLowerCase()">{{ requestForm.method }}</span>
            <el-input
              v-model="editingRequestName"
              class="request-name-input"
              placeholder="接口名称"
              size="small"
            />
            <template v-if="activeTestCase && activeTestCase !== 'default'">
              <span class="case-separator">/</span>
              <el-input
                v-model="editingCaseName"
                class="case-name-input"
                placeholder="用例名称"
                size="small"
              />
            </template>
          </div>
          <div class="dialog-actions">
            <el-button @click="handleSaveRequest">
              <el-icon><FolderChecked /></el-icon>
              保存
            </el-button>
            <el-button type="primary" :loading="sending" @click="handleSendRequest">
              <el-icon><Position /></el-icon>
              发送请求
            </el-button>
          </div>
        </div>
      </template>

      <div class="editor-content" v-if="selectedRequest">
        <div class="url-bar">
          <el-select v-model="requestForm.method" class="method-select" :class="requestForm.method.toLowerCase()">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="HEAD" value="HEAD" />
            <el-option label="OPTIONS" value="OPTIONS" />
          </el-select>
          <el-input
            v-model="requestForm.url"
            placeholder="输入请求 URL..."
            class="url-input"
            @keyup.enter="handleSendRequest"
          >
            <template #suffix>
              <el-tooltip content="环境变量" placement="top">
                <el-icon class="suffix-icon"><Coin /></el-icon>
              </el-tooltip>
            </template>
          </el-input>
        </div>

        <div class="editor-body">
          <div class="config-section">
            <div class="section-tabs">
              <div
                v-for="tab in requestTabs"
                :key="tab.name"
                class="section-tab"
                :class="{ active: activeRequestTab === tab.name }"
                @click="activeRequestTab = tab.name"
              >
                {{ tab.label }}
                <el-badge v-if="tab.count" :value="tab.count" type="primary" class="tab-badge" />
              </div>
            </div>

            <div class="section-content">
              <div v-show="activeRequestTab === 'params'" class="config-form">
                <div class="form-option">
                  <el-checkbox v-model="requestForm.urlEncode">URL 编码参数</el-checkbox>
                </div>
                <div class="kv-table">
                  <div class="kv-header">
                    <span class="col-check"></span>
                    <span class="col-key">参数名</span>
                    <span class="col-value">参数值</span>
                    <span class="col-desc">描述</span>
                    <span class="col-action"></span>
                  </div>
                  <div class="kv-body">
                    <div v-for="(param, index) in requestForm.params" :key="index" class="kv-row">
                      <el-checkbox v-model="param.enabled" class="col-check" />
                      <el-input v-model="param.key" placeholder="参数名" class="col-key" />
                      <el-input v-model="param.value" placeholder="参数值" class="col-value" />
                      <el-input v-model="param.description" placeholder="描述" class="col-desc" />
                      <el-button type="danger" link class="col-action" @click="removeParam(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="kv-footer" @click="addParam">
                    <el-icon><Plus /></el-icon>
                    <span>添加参数</span>
                  </div>
                </div>
              </div>

              <div v-show="activeRequestTab === 'headers'" class="config-form">
                <div class="form-option">
                  <el-checkbox v-model="requestForm.autoHeaders">自动添加常用请求头</el-checkbox>
                </div>
                <div class="kv-table">
                  <div class="kv-header">
                    <span class="col-check"></span>
                    <span class="col-key">请求头</span>
                    <span class="col-value">值</span>
                    <span class="col-desc">描述</span>
                    <span class="col-action"></span>
                  </div>
                  <div class="kv-body">
                    <div v-for="(header, index) in requestForm.headers" :key="index" class="kv-row">
                      <el-checkbox v-model="header.enabled" class="col-check" />
                      <el-input v-model="header.key" placeholder="请求头名称" class="col-key" />
                      <el-input v-model="header.value" placeholder="值" class="col-value" />
                      <el-input v-model="header.description" placeholder="描述" class="col-desc" />
                      <el-button type="danger" link class="col-action" @click="removeHeader(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="kv-footer" @click="addHeader">
                    <el-icon><Plus /></el-icon>
                    <span>添加请求头</span>
                  </div>
                </div>
              </div>

              <div v-show="activeRequestTab === 'body'" class="config-form">
                <div class="body-type-selector">
                  <el-radio-group v-model="requestForm.bodyType" size="small">
                    <el-radio-button label="none">无</el-radio-button>
                    <el-radio-button label="form-data">表单</el-radio-button>
                    <el-radio-button label="x-www-form-urlencoded">编码</el-radio-button>
                    <el-radio-button label="raw">原始</el-radio-button>
                    <el-radio-button label="binary">二进制</el-radio-button>
                  </el-radio-group>
                  <el-select v-if="requestForm.bodyType === 'raw'" v-model="requestForm.rawType" size="small" class="raw-type">
                    <el-option label="JSON" value="json" />
                    <el-option label="Text" value="text" />
                    <el-option label="JavaScript" value="javascript" />
                    <el-option label="HTML" value="html" />
                    <el-option label="XML" value="xml" />
                  </el-select>
                </div>
                <div v-if="requestForm.bodyType === 'none'" class="empty-body">
                  <span>此请求没有请求体</span>
                </div>
                <div v-else-if="requestForm.bodyType === 'raw'" class="raw-editor">
                  <el-input v-model="requestForm.rawBody" type="textarea" :rows="10" placeholder='{"key": "value"}' class="raw-textarea" />
                </div>
                <div v-else-if="requestForm.bodyType === 'form-data'" class="kv-table">
                  <div class="kv-header">
                    <span class="col-check"></span>
                    <span class="col-key">字段名</span>
                    <span class="col-value">值</span>
                    <span class="col-type">类型</span>
                    <span class="col-action"></span>
                  </div>
                  <div class="kv-body">
                    <div v-for="(item, index) in requestForm.formData" :key="index" class="kv-row">
                      <el-checkbox v-model="item.enabled" class="col-check" />
                      <el-input v-model="item.key" placeholder="字段名" class="col-key" />
                      <el-input v-model="item.value" placeholder="值" class="col-value" />
                      <el-select v-model="item.type" size="small" class="col-type">
                        <el-option label="文本" value="text" />
                        <el-option label="文件" value="file" />
                      </el-select>
                      <el-button type="danger" link class="col-action" @click="removeFormData(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="kv-footer" @click="addFormData">
                    <el-icon><Plus /></el-icon>
                    <span>添加字段</span>
                  </div>
                </div>
              </div>

              <div v-show="activeRequestTab === 'auth'" class="config-form">
                <div class="auth-config">
                  <div class="auth-row">
                    <span class="auth-label">认证方式</span>
                    <el-select v-model="requestForm.authType" class="auth-select">
                      <el-option label="无认证" value="none" />
                      <el-option label="API Key" value="api-key" />
                      <el-option label="Bearer Token" value="bearer" />
                      <el-option label="Basic Auth" value="basic" />
                      <el-option label="OAuth 2.0" value="oauth2" />
                    </el-select>
                  </div>
                  <div v-if="requestForm.authType === 'bearer'" class="auth-fields">
                    <div class="auth-field">
                      <span class="field-name">Token</span>
                      <el-input v-model="requestForm.authToken" placeholder="输入 Token" />
                    </div>
                  </div>
                  <div v-if="requestForm.authType === 'basic'" class="auth-fields">
                    <div class="auth-field">
                      <span class="field-name">用户名</span>
                      <el-input v-model="requestForm.authUsername" placeholder="输入用户名" />
                    </div>
                    <div class="auth-field">
                      <span class="field-name">密码</span>
                      <el-input v-model="requestForm.authPassword" type="password" placeholder="输入密码" show-password />
                    </div>
                  </div>
                  <div v-if="requestForm.authType === 'api-key'" class="auth-fields">
                    <div class="auth-field">
                      <span class="field-name">Key</span>
                      <el-input v-model="requestForm.authApiKey" placeholder="输入 Key" />
                    </div>
                    <div class="auth-field">
                      <span class="field-name">Value</span>
                      <el-input v-model="requestForm.authApiValue" placeholder="输入 Value" />
                    </div>
                    <div class="auth-field">
                      <span class="field-name">位置</span>
                      <el-select v-model="requestForm.authApiKeyLocation">
                        <el-option label="请求头" value="header" />
                        <el-option label="查询参数" value="query" />
                      </el-select>
                    </div>
                  </div>
                </div>
              </div>

              <div v-show="activeRequestTab === 'assertions'" class="config-form">
                <div class="assertion-config">
                  <div class="assertion-header">
                    <span>断言规则</span>
                    <el-button type="primary" link size="small" @click="addAssertion">
                      <el-icon><Plus /></el-icon>
                      添加
                    </el-button>
                  </div>
                  <div class="assertion-list">
                    <div v-for="(assertion, index) in currentAssertions" :key="index" class="assertion-item">
                      <el-select v-model="assertion.type" placeholder="类型" class="assertion-type">
                        <el-option label="状态码" value="status" />
                        <el-option label="响应时间" value="responseTime" />
                        <el-option label="响应体包含" value="bodyContains" />
                        <el-option label="JSON路径" value="jsonPath" />
                        <el-option label="响应头" value="header" />
                      </el-select>
                      <el-select v-model="assertion.operator" placeholder="操作" class="assertion-op">
                        <el-option label="等于" value="eq" />
                        <el-option label="不等于" value="neq" />
                        <el-option label="包含" value="contains" />
                        <el-option label="不包含" value="notContains" />
                        <el-option label="小于" value="lt" />
                        <el-option label="小于等于" value="lte" />
                        <el-option label="大于" value="gt" />
                        <el-option label="大于等于" value="gte" />
                      </el-select>
                      <el-input v-model="assertion.target" placeholder="目标" class="assertion-target" />
                      <el-input v-model="assertion.expected" placeholder="期望值" class="assertion-expected" />
                      <el-button type="danger" link @click="removeAssertion(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div v-if="currentAssertions.length === 0" class="empty-assertion">
                    <span>暂无断言规则</span>
                  </div>
                </div>
              </div>

              <div v-show="activeRequestTab === 'prerequest'" class="config-form">
                <div class="script-config">
                  <div class="script-header">
                    <span>前置脚本</span>
                    <el-button link type="primary" size="small">代码片段</el-button>
                  </div>
                  <el-input v-model="requestForm.preRequestScript" type="textarea" :rows="8" placeholder="// 请求发送前执行的脚本" class="script-textarea" />
                </div>
              </div>

              <div v-show="activeRequestTab === 'tests'" class="config-form">
                <div class="script-config">
                  <div class="script-header">
                    <span>测试脚本</span>
                    <el-button link type="primary" size="small">代码片段</el-button>
                  </div>
                  <el-input v-model="requestForm.testScript" type="textarea" :rows="8" placeholder="// 收到响应后执行的测试脚本" class="script-textarea" />
                </div>
              </div>
            </div>
          </div>

          <div class="response-section">
            <div class="response-header">
              <div class="response-meta">
                <template v-if="hasResponse">
                  <el-tag :type="responseStatusType" size="large" effect="dark">{{ response.status }}</el-tag>
                  <span class="meta-item">{{ response.time }}ms</span>
                  <span class="meta-item">{{ response.size }}</span>
                  <template v-if="activeTestCase !== 'default'">
                    <el-divider direction="vertical" />
                    <el-tag :type="assertionResult.passed === assertionResult.total ? 'success' : 'danger'" size="small">
                      断言 {{ assertionResult.passed }}/{{ assertionResult.total }}
                    </el-tag>
                  </template>
                </template>
                <span v-else class="meta-placeholder">发送请求后查看响应</span>
              </div>
              <div class="response-tabs">
                <div
                  v-for="tab in responseTabs"
                  :key="tab.name"
                  class="response-tab"
                  :class="{ active: activeResponseTab === tab.name }"
                  @click="activeResponseTab = tab.name"
                >
                  {{ tab.label }}
                </div>
              </div>
            </div>

            <div class="response-content">
              <div v-show="activeResponseTab === 'body'" class="response-body-panel">
                <template v-if="hasResponse">
                  <div class="body-toolbar">
                    <el-radio-group v-model="responseBodyView" size="small">
                      <el-radio-button label="pretty">格式化</el-radio-button>
                      <el-radio-button label="raw">原始</el-radio-button>
                      <el-radio-button label="preview">预览</el-radio-button>
                    </el-radio-group>
                    <el-select v-if="responseBodyView === 'pretty'" v-model="responseBodyFormat" size="small" class="format-select">
                      <el-option label="JSON" value="json" />
                      <el-option label="XML" value="xml" />
                      <el-option label="HTML" value="html" />
                      <el-option label="Text" value="text" />
                    </el-select>
                    <el-button link size="small" @click="copyResponseBody">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                  </div>
                  <div class="body-content">
                    <pre v-if="responseBodyView === 'pretty'" class="response-code"><code>{{ formattedResponseBody }}</code></pre>
                    <pre v-else class="response-code">{{ response.body }}</pre>
                  </div>
                </template>
                <div v-else class="empty-response">
                  <span>发送请求后查看响应</span>
                </div>
              </div>

              <div v-show="activeResponseTab === 'headers'" class="response-headers-panel">
                <template v-if="hasResponse">
                  <div class="headers-list">
                    <div v-for="(value, key) in response.headers" :key="key" class="header-item">
                      <span class="header-key">{{ key }}</span>
                      <span class="header-value">{{ value }}</span>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-response">
                  <span>发送请求后查看响应头</span>
                </div>
              </div>

              <div v-show="activeResponseTab === 'cookies'" class="response-cookies-panel">
                <template v-if="hasResponse && response.cookies?.length">
                  <div class="cookies-list">
                    <div v-for="(cookie, index) in response.cookies" :key="index" class="cookie-item">
                      <span class="cookie-key">{{ cookie.name }}</span>
                      <span class="cookie-value">{{ cookie.value }}</span>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-response">
                  <span>没有 Cookies</span>
                </div>
              </div>

              <div v-show="activeResponseTab === 'assertionResults'" class="response-assertion-panel">
                <template v-if="hasResponse">
                  <div class="assertion-results">
                    <div v-for="(result, index) in assertionResults" :key="index" class="result-item" :class="{ passed: result.passed, failed: !result.passed }">
                      <el-icon v-if="result.passed" color="var(--color-success)"><CircleCheck /></el-icon>
                      <el-icon v-else color="var(--color-danger)"><CircleClose /></el-icon>
                      <span class="result-message">{{ result.message }}</span>
                      <span class="result-detail">{{ result.detail }}</span>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-response">
                  <span>发送请求后查看断言结果</span>
                </div>
              </div>

              <div v-show="activeResponseTab === 'tests'" class="response-tests-panel">
                <template v-if="hasResponse && response.testResults?.length">
                  <div class="tests-list">
                    <div v-for="(test, index) in response.testResults" :key="index" class="test-item" :class="{ passed: test.passed, failed: !test.passed }">
                      <el-icon v-if="test.passed" color="var(--color-success)"><CircleCheck /></el-icon>
                      <el-icon v-else color="var(--color-danger)"><CircleClose /></el-icon>
                      <span class="test-name">{{ test.name }}</span>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-response">
                  <span>没有测试结果</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="saveDialogVisible" title="保存请求" width="480px">
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="请求名称">
          <el-input v-model="saveForm.name" placeholder="请输入请求名称" />
        </el-form-item>
        <el-form-item label="请求描述">
          <el-input v-model="saveForm.description" type="textarea" :rows="3" placeholder="请输入请求描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveRequest">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="testCaseDialogVisible" :title="editingTestCase ? '编辑测试用例' : '新建测试用例'" width="480px">
      <el-form :model="testCaseSaveForm" label-width="80px">
        <el-form-item label="用例名称">
          <el-input v-model="testCaseSaveForm.name" placeholder="请输入测试用例名称" />
        </el-form-item>
        <el-form-item label="用例描述">
          <el-input v-model="testCaseSaveForm.description" type="textarea" :rows="3" placeholder="请输入测试用例描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testCaseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveTestCase">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import {
  Plus,
  Search,
  Folder,
  FolderAdd,
  FolderChecked,
  Document,
  Position,
  Delete,
  MoreFilled,
  Coin,
  CopyDocument,
  CircleCheck,
  CircleClose,
  Collection,
  Edit,
  ArrowLeft,
  ArrowRight,
  VideoPlay,
  Operation,
  InfoFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

defineProps({
  project: {
    type: Object,
    required: true
  }
})

const treeRef = ref(null)
const panelWidth = ref(280)
const panelCollapsed = ref(false)
const sidebarSearch = ref('')
const selectedRequest = ref(null)
const viewMode = ref('none')
const activeTestCase = ref('default')
const editingRequestName = ref('')
const editingCaseName = ref('')
const isNewCase = ref(false)
const activeRequestTab = ref('params')
const activeResponseTab = ref('body')
const sending = ref(false)
const hasResponse = ref(false)
const editorDialogVisible = ref(false)

const responseBodyView = ref('pretty')
const responseBodyFormat = ref('json')

const saveDialogVisible = ref(false)
const saveForm = reactive({
  name: '',
  description: ''
})

const testCaseDialogVisible = ref(false)
const editingTestCase = ref(null)
const testCaseSaveForm = reactive({
  name: '',
  description: ''
})

const selectedCaseIds = ref([])
const batchMode = ref(false)
const allCasesTableRef = ref(null)
const singleCasesTableRef = ref(null)

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedCaseIds.value = []
    allCasesTableRef.value?.clearSelection()
    singleCasesTableRef.value?.clearSelection()
  }
}

const handleBatchAction = async (action) => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先选择用例后再进行批量操作')
    return
  }

  const handlers = {
    execute: handleBatchExecute,
    copy: handleBatchCopy,
    delete: handleBatchDelete
  }

  const success = await handlers[action]?.()
  if (success) {
    batchMode.value = false
    selectedCaseIds.value = []
    allCasesTableRef.value?.clearSelection()
  }
}

const handleBatchExecute = async () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return false
  }
  ElMessage.info(`开始批量执行 ${selectedCaseIds.value.length} 个用例...`)
  for (const testCase of selectedCaseIds.value) {
    await runSingleCase(testCase, true)
  }
  ElMessage.success(`已完成 ${selectedCaseIds.value.length} 个用例执行`)
  return true
}

const handleBatchCopy = () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先选择要复制的用例')
    return false
  }
  ElMessage.info('批量复制功能开发中')
  return false
}

const handleBatchDelete = async () => {
  if (selectedCaseIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的用例')
    return false
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCaseIds.value.length} 个用例吗？`, '警告', {
      type: 'warning'
    })
    const deletedCount = selectedCaseIds.value.length
    if (viewMode.value === 'single' && selectedRequest.value) {
      for (const testCase of selectedCaseIds.value) {
        const index = selectedRequest.value.testCases?.findIndex(t => t.id === testCase.id)
        if (index !== undefined && index > -1) {
          selectedRequest.value.testCases.splice(index, 1)
        }
      }
    } else {
      for (const testCase of selectedCaseIds.value) {
        const request = findRequestById(testCase.requestId)
        if (request) {
          const index = request.testCases?.findIndex(t => t.id === testCase.id)
          if (index !== undefined && index > -1) {
            request.testCases.splice(index, 1)
          }
        }
      }
    }
    ElMessage.success(`成功删除 ${deletedCount} 个用例`)
    return true
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '批量删除失败')
    }
    return false
  }
}

const allTestCases = computed(() => {
  const cases = []
  const collectCases = (nodes) => {
    for (const node of nodes) {
      if (node.type === 'request' && node.testCases?.length) {
        for (const tc of node.testCases) {
          cases.push({
            id: tc.id,
            caseName: tc.name,
            requestName: node.name,
            requestId: node.id,
            method: tc.request?.method || node.method,
            url: tc.request?.url || node.url,
            assertionCount: tc.assertions?.length || 0,
            lastResult: tc.lastResult || null,
            lastResponse: tc.lastResponse || null,
            request: tc.request,
            assertions: tc.assertions
          })
        }
      }
      if (node.children) {
        collectCases(node.children)
      }
    }
  }
  collectCases(collectionTree.value)
  return cases
})

const formatRequestParams = (request) => {
  if (!request) return '-'

  const parts = []

  if (request.params?.length) {
    const enabledParams = request.params.filter(p => p.enabled && p.key)
    if (enabledParams.length) {
      parts.push(enabledParams.map(p => `${p.key}=${p.value}`).join(', '))
    }
  }

  if (request.rawBody) {
    const bodyPreview = truncateText(request.rawBody, 30)
    parts.push(`Body: ${bodyPreview}`)
  }

  if (request.formData?.length) {
    const enabledForm = request.formData.filter(f => f.enabled && f.key)
    if (enabledForm.length) {
      parts.push(enabledForm.map(f => `${f.key}=${f.value}`).join(', '))
    }
  }

  return parts.length > 0 ? parts.join(' | ') : '-'
}

const truncateText = (text, maxLength = 50) => {
  if (!text) return ''
  const str = typeof text === 'object' ? JSON.stringify(text) : String(text)
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength) + '...'
}

const handleCaseSelectionChange = (selection) => {
  selectedCaseIds.value = selection
}

const runSingleCase = async (row, silent = false) => {
  try {
    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200))

    const passed = Math.random() > 0.3
    const status = passed ? 200 : 400
    const responseBody = passed
      ? JSON.stringify({ code: 0, message: 'success', data: { id: 1, name: 'test' } })
      : JSON.stringify({ code: -1, message: 'error', error: 'Bad Request' })

    const responseData = {
      status,
      body: responseBody
    }

    updateCaseResult(row.requestId, row.id, passed ? 'passed' : 'failed', responseData)
    row.lastResult = passed ? 'passed' : 'failed'
    row.lastResponse = responseData

    if (!silent) {
      if (passed) {
        ElMessage.success(`测试用例 "${row.caseName}" 通过`)
      } else {
        ElMessage.error(`测试用例 "${row.caseName}" 失败`)
      }
    }
  } catch {
    updateCaseResult(row.requestId, row.id, 'failed', null)
    row.lastResult = 'failed'
    row.lastResponse = null
  }
}

const updateCaseResult = (requestId, caseId, result, responseData = null) => {
  const findAndUpdate = (nodes) => {
    for (const node of nodes) {
      if (node.id === requestId && node.testCases) {
        const tc = node.testCases.find(t => t.id === caseId)
        if (tc) {
          tc.lastResult = result
          tc.lastResponse = responseData
          return true
        }
      }
      if (node.children && findAndUpdate(node.children)) {
        return true
      }
    }
    return false
  }
  findAndUpdate(collectionTree.value)
}

const editCaseFromManager = (row) => {
  const request = findRequestById(row.requestId)
  if (request) {
    selectedRequest.value = request
    editingRequestName.value = request.name
    viewMode.value = 'single'
    isNewCase.value = false
    activeTestCase.value = row.id
    editingCaseName.value = row.caseName
    hasResponse.value = false
    assertionResults.value = []
    const tc = request.testCases?.find(t => t.id === row.id)
    if (tc) {
      loadRequestConfig(tc.request || {
        method: request.method,
        url: request.url
      })
      if (tc.lastResponse) {
        hasResponse.value = true
        response.value = {
          status: tc.lastResponse.status,
          statusText: tc.lastResponse.status < 400 ? 'OK' : 'Error',
          headers: {},
          body: tc.lastResponse.body,
          time: 0,
          size: tc.lastResponse.body?.length || 0
        }
      }
    }
    editorDialogVisible.value = true
  }
}

const deleteCaseFromManager = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试用例 "${row.caseName}" 吗？`, '确认删除', {
      type: 'warning'
    })

    const request = findRequestById(row.requestId)
    if (request) {
      const index = request.testCases?.findIndex(t => t.id === row.id)
      if (index !== undefined && index > -1) {
        request.testCases.splice(index, 1)
        ElMessage.success('删除成功')
      }
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const collectionTree = ref([
  {
    id: 1,
    name: '用户管理',
    type: 'folder',
    children: [
      { id: 11, name: '获取用户列表', type: 'request', method: 'GET', url: '/api/v1/users', testCases: [] },
      { id: 12, name: '创建用户', type: 'request', method: 'POST', url: '/api/v1/users', testCases: [] },
      { id: 13, name: '获取用户详情', type: 'request', method: 'GET', url: '/api/v1/users/:id', testCases: [] },
      { id: 14, name: '更新用户', type: 'request', method: 'PUT', url: '/api/v1/users/:id', testCases: [] },
      { id: 15, name: '删除用户', type: 'request', method: 'DELETE', url: '/api/v1/users/:id', testCases: [] }
    ]
  },
  {
    id: 2,
    name: '订单管理',
    type: 'folder',
    children: [
      { id: 21, name: '获取订单列表', type: 'request', method: 'GET', url: '/api/v1/orders', testCases: [] },
      { id: 22, name: '创建订单', type: 'request', method: 'POST', url: '/api/v1/orders', testCases: [] }
    ]
  },
  {
    id: 3,
    name: '支付管理',
    type: 'folder',
    children: [
      { id: 31, name: '支付订单', type: 'request', method: 'POST', url: '/api/v1/orders/:id/pay', testCases: [] },
      { id: 32, name: '退款', type: 'request', method: 'POST', url: '/api/v1/orders/:id/refund', testCases: [] }
    ]
  }
])

const requestForm = reactive({
  method: 'GET',
  url: '',
  urlEncode: true,
  autoHeaders: true,
  params: [{ key: '', value: '', description: '', enabled: true }],
  headers: [
    { key: 'Content-Type', value: 'application/json', description: '', enabled: true },
    { key: '', value: '', description: '', enabled: true }
  ],
  bodyType: 'none',
  rawType: 'json',
  rawBody: '',
  formData: [{ key: '', value: '', type: 'text', enabled: true }],
  authType: 'none',
  authToken: '',
  authUsername: '',
  authPassword: '',
  authApiKey: '',
  authApiValue: '',
  authApiKeyLocation: 'header',
  preRequestScript: '',
  testScript: ''
})

const response = reactive({
  status: 200,
  time: 0,
  size: '0 B',
  body: '',
  headers: {},
  cookies: [],
  testResults: []
})

const assertionResult = ref({ passed: 0, total: 0 })
const assertionResults = ref([])

const requestTabs = computed(() => {
  const tabs = [
    { name: 'params', label: '参数', count: paramsCount.value },
    { name: 'headers', label: '请求头', count: headersCount.value },
    { name: 'body', label: '请求体', count: 0 },
    { name: 'auth', label: '认证', count: 0 },
    { name: 'prerequest', label: '前置脚本', count: 0 },
    { name: 'tests', label: '测试脚本', count: 0 }
  ]
  if (activeTestCase.value !== 'default') {
    tabs.splice(4, 0, { name: 'assertions', label: '断言', count: 0 })
  }
  return tabs
})

const responseTabs = computed(() => {
  const tabs = [
    { name: 'body', label: '响应体' },
    { name: 'headers', label: '响应头' },
    { name: 'cookies', label: 'Cookies' },
    { name: 'tests', label: '测试结果' }
  ]
  if (activeTestCase.value !== 'default') {
    tabs.splice(3, 0, { name: 'assertionResults', label: '断言结果' })
  }
  return tabs
})

const currentAssertions = computed(() => {
  if (activeTestCase.value === 'default' || !selectedRequest.value) {
    return []
  }
  const tc = selectedRequest.value.testCases?.find(t => t.id === activeTestCase.value)
  return tc?.assertions || []
})

const treeProps = {
  label: 'name',
  children: 'children'
}

const filteredCollectionTree = computed(() => {
  if (!sidebarSearch.value) {
    return collectionTree.value
  }

  const search = sidebarSearch.value.toLowerCase()
  const filterTree = (nodes) => {
    return nodes.reduce((acc, node) => {
      if (node.name.toLowerCase().includes(search)) {
        acc.push(node)
      } else if (node.children) {
        const filteredChildren = filterTree(node.children)
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren })
        }
      }
      return acc
    }, [])
  }
  return filterTree(collectionTree.value)
})

const paramsCount = computed(() => {
  return requestForm.params.filter(p => p.enabled && p.key).length
})

const headersCount = computed(() => {
  return requestForm.headers.filter(h => h.enabled && h.key).length
})

const responseStatusType = computed(() => {
  const status = response.status
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400) return 'danger'
  return 'info'
})

const formattedResponseBody = computed(() => {
  if (!response.body) return ''
  try {
    if (responseBodyFormat.value === 'json') {
      return JSON.stringify(JSON.parse(response.body), null, 2)
    }
    return response.body
  } catch {
    return response.body
  }
})

const startResize = (e) => {
  const startX = e.clientX
  const startWidth = panelWidth.value

  const onMouseMove = (e) => {
    const diff = e.clientX - startX
    panelWidth.value = Math.max(200, Math.min(400, startWidth + diff))
  }

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const showAllCases = () => {
  viewMode.value = 'all'
  selectedRequest.value = null
}

const selectRequest = (request) => {
  selectedRequest.value = request
  viewMode.value = 'single'
  activeTestCase.value = 'default'
  hasResponse.value = false
  assertionResults.value = []
  loadRequestConfig(request.request || {
    method: request.method,
    url: request.url
  })
}

const handleNodeClick = (data) => {
  if (data.type === 'request') {
    selectRequest(data)
  }
}

const handleEditorClose = () => {
  isNewCase.value = false
  activeTestCase.value = 'default'
}

const runSelectedRequestCases = async () => {
  if (!selectedRequest.value?.testCases?.length) return

  const cases = selectedRequest.value.testCases
  ElMessage.info(`开始运行 ${cases.length} 个测试用例...`)

  for (const tc of cases) {
    await runSingleCaseForRequest(selectedRequest.value.id, tc)
  }

  ElMessage.success(`已完成 ${cases.length} 个测试用例运行`)
}

const runSingleCaseForRequest = async (requestId, testCase) => {
  try {
    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200))
    const passed = Math.random() > 0.3
    testCase.lastResult = passed ? 'passed' : 'failed'
  } catch {
    testCase.lastResult = 'failed'
  }
}

const editTestCase = (testCase) => {
  if (selectedRequest.value) {
    isNewCase.value = false
    editingRequestName.value = selectedRequest.value.name
    activeTestCase.value = testCase.id
    editingCaseName.value = testCase.name
    hasResponse.value = false
    assertionResults.value = []
    loadRequestConfig(testCase.request || {
      method: selectedRequest.value.method,
      url: selectedRequest.value.url
    })
    if (testCase.lastResponse) {
      hasResponse.value = true
      response.value = {
        status: testCase.lastResponse.status,
        statusText: testCase.lastResponse.status < 400 ? 'OK' : 'Error',
        headers: {},
        body: testCase.lastResponse.body,
        time: 0,
        size: testCase.lastResponse.body?.length || 0
      }
    }
    editorDialogVisible.value = true
  }
}

const deleteTestCase = async (testCase) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试用例 "${testCase.name}" 吗？`, '确认删除', {
      type: 'warning'
    })

    if (selectedRequest.value) {
      const index = selectedRequest.value.testCases?.findIndex(t => t.id === testCase.id)
      if (index !== undefined && index > -1) {
        selectedRequest.value.testCases.splice(index, 1)
        ElMessage.success('删除成功')
      }
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const findRequestById = (id) => {
  const findInTree = (nodes) => {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children) {
        const found = findInTree(node.children)
        if (found) return found
      }
    }
    return null
  }
  return findInTree(collectionTree.value)
}

const handleNodeCommand = (command, data) => {
  switch (command) {
    case 'addRequest':
      handleAddRequest(data.id)
      break
    case 'addFolder':
      handleAddFolder(data.id)
      break
    case 'addTestCase':
      if (data.type === 'request') {
        selectedRequest.value = data
        handleAddTestCase()
      }
      break
    case 'edit':
      ElMessage.info('编辑功能开发中')
      break
    case 'duplicate':
      ElMessage.info('复制功能开发中')
      break
    case 'delete':
      handleDeleteNode(data)
      break
  }
}

const handleDeleteNode = async (data) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${data.name}" 吗？`, '确认删除', {
      type: 'warning'
    })

    const deleteFromTree = (nodes, id) => {
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].id === id) {
          nodes.splice(i, 1)
          return true
        }
        if (nodes[i].children && deleteFromTree(nodes[i].children, id)) {
          return true
        }
      }
      return false
    }
    deleteFromTree(collectionTree.value, data.id)
    if (selectedRequest.value?.id === data.id) {
      selectedRequest.value = null
      editorDialogVisible.value = false
    }
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleAddFolder = async (parentId = null) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValidator: (val) => {
        if (!val || val.trim() === '') return '文件夹名称不能为空'
        return true
      }
    })

    const newFolder = {
      id: Date.now(),
      name: value.trim(),
      type: 'folder',
      children: []
    }

    if (parentId) {
      const addToParent = (nodes) => {
        for (const node of nodes) {
          if (node.id === parentId) {
            if (!node.children) node.children = []
            node.children.push(newFolder)
            return true
          }
          if (node.children && addToParent(node.children)) {
            return true
          }
        }
        return false
      }
      addToParent(collectionTree.value)
    } else {
      collectionTree.value.push(newFolder)
    }
    ElMessage.success('文件夹创建成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('创建失败')
    }
  }
}

const handleAddRequest = (parentId = null) => {
  const newRequest = {
    id: Date.now(),
    name: 'New Request',
    type: 'request',
    method: 'GET',
    url: '',
    testCases: [],
    request: createDefaultRequestConfig()
  }

  if (parentId) {
    const addToParent = (nodes) => {
      for (const node of nodes) {
        if (node.id === parentId) {
          if (!node.children) node.children = []
          node.children.push(newRequest)
          return true
        }
        if (node.children && addToParent(node.children)) {
          return true
        }
      }
      return false
    }
    addToParent(collectionTree.value)
  } else {
    collectionTree.value.push(newRequest)
  }

  selectedRequest.value = newRequest
  editingRequestName.value = newRequest.name
  isNewCase.value = false
  activeTestCase.value = 'default'
  hasResponse.value = false
  assertionResults.value = []
  loadRequestConfig(newRequest.request)
  editorDialogVisible.value = true
}

const handleAddTestCase = () => {
  if (!selectedRequest.value) return

  isNewCase.value = true
  editingRequestName.value = selectedRequest.value.name
  activeTestCase.value = 'new'
  editingCaseName.value = '新用例'
  hasResponse.value = false
  assertionResults.value = []
  loadRequestConfig(createDefaultRequestConfig())
  editorDialogVisible.value = true
}

const openAddTestCase = (request) => {
  selectedRequest.value = request
  editingRequestName.value = request.name
  viewMode.value = 'single'
  isNewCase.value = true
  activeTestCase.value = 'new'
  editingCaseName.value = '新用例'
  hasResponse.value = false
  assertionResults.value = []
  loadRequestConfig(createDefaultRequestConfig())
  editorDialogVisible.value = true
}

const openTestCase = (request, testCase) => {
  selectedRequest.value = request
  editingRequestName.value = request.name
  viewMode.value = 'single'
  isNewCase.value = false
  activeTestCase.value = testCase.id
  editingCaseName.value = testCase.name
  hasResponse.value = false
  assertionResults.value = []
  loadRequestConfig(testCase.request || {
    method: request.method,
    url: request.url
  })
  if (testCase.lastResponse) {
    hasResponse.value = true
    response.value = {
      status: testCase.lastResponse.status,
      statusText: testCase.lastResponse.status < 400 ? 'OK' : 'Error',
      headers: {},
      body: testCase.lastResponse.body,
      time: 0,
      size: testCase.lastResponse.body?.length || 0
    }
  }
  editorDialogVisible.value = true
}

const createDefaultRequestConfig = () => ({
  method: 'GET',
  url: '',
  params: [{ key: '', value: '', description: '', enabled: true }],
  headers: [
    { key: 'Content-Type', value: 'application/json', description: '', enabled: true },
    { key: '', value: '', description: '', enabled: true }
  ],
  bodyType: 'none',
  rawType: 'json',
  rawBody: '',
  formData: [{ key: '', value: '', type: 'text', enabled: true }],
  authType: 'none',
  authToken: '',
  authUsername: '',
  authPassword: '',
  authApiKey: '',
  authApiValue: '',
  authApiKeyLocation: 'header',
  preRequestScript: '',
  testScript: '',
  urlEncode: true,
  autoHeaders: true
})

const getCurrentRequestConfig = () => ({
  method: requestForm.method,
  url: requestForm.url,
  params: JSON.parse(JSON.stringify(requestForm.params)),
  headers: JSON.parse(JSON.stringify(requestForm.headers)),
  bodyType: requestForm.bodyType,
  rawType: requestForm.rawType,
  rawBody: requestForm.rawBody,
  formData: JSON.parse(JSON.stringify(requestForm.formData)),
  authType: requestForm.authType,
  authToken: requestForm.authToken,
  authUsername: requestForm.authUsername,
  authPassword: requestForm.authPassword,
  authApiKey: requestForm.authApiKey,
  authApiValue: requestForm.authApiValue,
  authApiKeyLocation: requestForm.authApiKeyLocation,
  preRequestScript: requestForm.preRequestScript,
  testScript: requestForm.testScript,
  urlEncode: requestForm.urlEncode,
  autoHeaders: requestForm.autoHeaders
})

const loadRequestConfig = (config) => {
  if (!config) {
    config = createDefaultRequestConfig()
  }
  requestForm.method = config.method || 'GET'
  requestForm.url = config.url || ''
  requestForm.params = config.params ? JSON.parse(JSON.stringify(config.params)) : [{ key: '', value: '', description: '', enabled: true }]
  requestForm.headers = config.headers ? JSON.parse(JSON.stringify(config.headers)) : [
    { key: 'Content-Type', value: 'application/json', description: '', enabled: true },
    { key: '', value: '', description: '', enabled: true }
  ]
  requestForm.bodyType = config.bodyType || 'none'
  requestForm.rawType = config.rawType || 'json'
  requestForm.rawBody = config.rawBody || ''
  requestForm.formData = config.formData ? JSON.parse(JSON.stringify(config.formData)) : [{ key: '', value: '', type: 'text', enabled: true }]
  requestForm.authType = config.authType || 'none'
  requestForm.authToken = config.authToken || ''
  requestForm.authUsername = config.authUsername || ''
  requestForm.authPassword = config.authPassword || ''
  requestForm.authApiKey = config.authApiKey || ''
  requestForm.authApiValue = config.authApiValue || ''
  requestForm.authApiKeyLocation = config.authApiKeyLocation || 'header'
  requestForm.preRequestScript = config.preRequestScript || ''
  requestForm.testScript = config.testScript || ''
  requestForm.urlEncode = config.urlEncode !== undefined ? config.urlEncode : true
  requestForm.autoHeaders = config.autoHeaders !== undefined ? config.autoHeaders : true
}

const saveCurrentConfigToTestCase = () => {
  if (!selectedRequest.value) return

  selectedRequest.value.name = editingRequestName.value

  if (isNewCase.value) {
    const newTestCase = {
      id: Date.now(),
      name: editingCaseName.value || '新用例',
      description: '',
      request: getCurrentRequestConfig(),
      assertions: []
    }

    if (!selectedRequest.value.testCases) {
      selectedRequest.value.testCases = []
    }
    selectedRequest.value.testCases.push(newTestCase)
    isNewCase.value = false
  } else if (activeTestCase.value === 'default') {
    selectedRequest.value.method = requestForm.method
    selectedRequest.value.url = requestForm.url
    selectedRequest.value.request = getCurrentRequestConfig()
  } else {
    const tc = selectedRequest.value.testCases?.find(t => t.id === activeTestCase.value)
    if (tc) {
      tc.name = editingCaseName.value
      tc.request = getCurrentRequestConfig()
    }
  }
}

const handleSaveRequest = () => {
  if (!selectedRequest.value) return
  saveCurrentConfigToTestCase()
  ElMessage.success('保存成功')
  editorDialogVisible.value = false
}

const confirmSaveRequest = () => {
  if (!saveForm.name) {
    ElMessage.warning('请输入请求名称')
    return
  }

  if (selectedRequest.value) {
    selectedRequest.value.name = saveForm.name
    selectedRequest.value.request = getCurrentRequestConfig()
    selectedRequest.value.method = requestForm.method
    selectedRequest.value.url = requestForm.url
  }

  saveDialogVisible.value = false
  ElMessage.success('保存成功')
}

const confirmSaveTestCase = () => {
  if (!testCaseSaveForm.name) {
    ElMessage.warning('请输入测试用例名称')
    return
  }

  if (editingTestCase.value) {
    editingTestCase.value.name = testCaseSaveForm.name
    editingTestCase.value.description = testCaseSaveForm.description
    ElMessage.success('测试用例更新成功')
  } else {
    const newTestCase = {
      id: Date.now(),
      name: testCaseSaveForm.name,
      description: testCaseSaveForm.description,
      assertions: [{ type: 'status', operator: 'eq', target: '', expected: '200' }],
      request: getCurrentRequestConfig()
    }

    if (!selectedRequest.value.testCases) {
      selectedRequest.value.testCases = []
    }
    selectedRequest.value.testCases.push(newTestCase)
    activeTestCase.value = newTestCase.id
    ElMessage.success('测试用例创建成功')
  }

  testCaseDialogVisible.value = false
}

const handleSendRequest = async () => {
  if (!requestForm.url) {
    ElMessage.warning('请输入请求 URL')
    return
  }

  sending.value = true
  const startTime = Date.now()

  try {
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 500))

    response.status = 200
    response.time = Date.now() - startTime
    response.size = '1.2 KB'
    response.body = JSON.stringify({
      code: 0,
      message: 'success',
      data: {
        id: 1,
        name: '示例数据',
        items: [
          { id: 1, title: '项目 1' },
          { id: 2, title: '项目 2' },
          { id: 3, title: '项目 3' }
        ]
      }
    })
    response.headers = {
      'Content-Type': 'application/json',
      'X-Request-Id': 'req-' + Date.now(),
      'X-Response-Time': response.time + 'ms'
    }
    response.cookies = []
    response.testResults = [
      { name: 'Status code is 200', passed: true },
      { name: 'Response has data field', passed: true }
    ]

    hasResponse.value = true
    activeResponseTab.value = 'body'

    if (activeTestCase.value !== 'default') {
      runAssertions()
    }
  } catch (error) {
    response.status = 500
    response.body = JSON.stringify({ error: error.message })
    hasResponse.value = true
  } finally {
    sending.value = false
  }
}

const runAssertions = () => {
  const tc = selectedRequest.value?.testCases?.find(t => t.id === activeTestCase.value)
  if (!tc?.assertions) {
    assertionResults.value = []
    assertionResult.value = { passed: 0, total: 0 }
    return
  }

  const results = []
  let passed = 0

  for (const assertion of tc.assertions) {
    const result = {
      passed: false,
      message: '',
      detail: ''
    }

    switch (assertion.type) {
      case 'status':
        result.message = `状态码 ${getOperatorLabel(assertion.operator)} ${assertion.expected}`
        result.passed = compareValues(response.status, assertion.operator, parseInt(assertion.expected))
        result.detail = `实际: ${response.status}`
        break
      case 'responseTime':
        result.message = `响应时间 ${getOperatorLabel(assertion.operator)} ${assertion.expected}ms`
        result.passed = compareValues(response.time, assertion.operator, parseInt(assertion.expected))
        result.detail = `实际: ${response.time}ms`
        break
      case 'bodyContains':
        result.message = `响应体包含 "${assertion.expected}"`
        result.passed = response.body.includes(assertion.expected)
        result.detail = result.passed ? '已找到' : '未找到'
        break
      case 'jsonPath':
        result.message = `JSON路径 ${assertion.target} ${getOperatorLabel(assertion.operator)} ${assertion.expected}`
        try {
          const json = JSON.parse(response.body)
          const value = getJsonValueByPath(json, assertion.target)
          result.passed = compareValues(value, assertion.operator, assertion.expected)
          result.detail = `实际: ${value}`
        } catch {
          result.passed = false
          result.detail = 'JSON解析失败'
        }
        break
      case 'header': {
        result.message = `响应头 ${assertion.target} ${getOperatorLabel(assertion.operator)} ${assertion.expected}`
        const headerValue = response.headers[assertion.target]
        result.passed = compareValues(headerValue, assertion.operator, assertion.expected)
        result.detail = `实际: ${headerValue || '不存在'}`
        break
      }
    }

    if (result.passed) passed++
    results.push(result)
  }

  assertionResults.value = results
  assertionResult.value = { passed, total: results.length }
}

const getOperatorLabel = (operator) => {
  const labels = {
    eq: '等于',
    neq: '不等于',
    contains: '包含',
    notContains: '不包含',
    lt: '小于',
    lte: '小于等于',
    gt: '大于',
    gte: '大于等于'
  }
  return labels[operator] || operator
}

const compareValues = (actual, operator, expected) => {
  switch (operator) {
    case 'eq': return actual == expected
    case 'neq': return actual != expected
    case 'contains': return String(actual).includes(expected)
    case 'notContains': return !String(actual).includes(expected)
    case 'lt': return actual < expected
    case 'lte': return actual <= expected
    case 'gt': return actual > expected
    case 'gte': return actual >= expected
    default: return false
  }
}

const getJsonValueByPath = (obj, path) => {
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.')
  let result = obj
  for (const key of keys) {
    if (result === null || result === undefined) return undefined
    result = result[key]
  }
  return result
}

const addParam = () => {
  requestForm.params.push({ key: '', value: '', description: '', enabled: true })
}

const removeParam = (index) => {
  requestForm.params.splice(index, 1)
}

const addHeader = () => {
  requestForm.headers.push({ key: '', value: '', description: '', enabled: true })
}

const removeHeader = (index) => {
  requestForm.headers.splice(index, 1)
}

const addFormData = () => {
  requestForm.formData.push({ key: '', value: '', type: 'text', enabled: true })
}

const removeFormData = (index) => {
  requestForm.formData.splice(index, 1)
}

const addAssertion = () => {
  const tc = selectedRequest.value?.testCases?.find(t => t.id === activeTestCase.value)
  if (tc) {
    if (!tc.assertions) tc.assertions = []
    tc.assertions.push({ type: 'status', operator: 'eq', target: '', expected: '' })
  }
}

const removeAssertion = (index) => {
  const tc = selectedRequest.value?.testCases?.find(t => t.id === activeTestCase.value)
  if (tc?.assertions) {
    tc.assertions.splice(index, 1)
  }
}

const copyResponseBody = async () => {
  try {
    await navigator.clipboard.writeText(response.body)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.interface-tester {
  height: 100%;
  background: var(--color-bg-secondary);
  display: flex;
  flex-direction: column;
}

.tester-layout {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.collection-wrapper {
  position: relative;
  flex-shrink: 0;
  transition: width 0.3s ease;
  display: flex;
  min-width: 24px;
}

.collection-panel {
  background: #fff;
  border-right: 1px solid var(--color-border-primary);
  display: flex;
  flex-direction: column;
  position: relative;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.collection-panel.collapsed {
  border-right: none;
}

.panel-resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s;
  z-index: 10;
}

.panel-resize-handle:hover {
  background: var(--color-primary);
}

.sidebar-toggle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 80px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: left 0.3s ease;
}

.sidebar-toggle:hover {
  background: rgba(0, 0, 0, 0.02);
}

.sidebar-toggle:hover .el-icon {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.sidebar-toggle .el-icon {
  font-size: 22px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  border-radius: 50%;
  padding: 8px;
  transition: all 0.2s ease;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-primary);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-title.clickable {
  cursor: pointer;
  padding: 4px 8px;
  margin: -4px -8px;
  border-radius: 2px;
  transition: background 0.2s;
}

.header-title.clickable:hover {
  background: var(--color-bg-secondary);
}

.title-icon {
  color: var(--color-primary);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.panel-search {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-primary);
}

.panel-search :deep(.el-input__wrapper) {
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.collection-tree {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.collection-tree :deep(.el-tree) {
  background: transparent;
}

.collection-tree :deep(.el-tree-node__content) {
  height: 32px;
  border-radius: 2px;
}

.collection-tree :deep(.el-tree-node__content:hover) {
  background: var(--color-bg-secondary);
}

.collection-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--color-primary-light);
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 4px;
}

.node-left {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

.method-indicator {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 2px;
  text-transform: uppercase;
}

.method-indicator.get,
.method-indicator.post,
.method-indicator.put,
.method-indicator.patch,
.method-indicator.delete {
  background: var(--color-success-light);
  color: var(--color-success);
}

.method-indicator.post {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.method-indicator.put {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.method-indicator.patch {
  background: var(--color-info-light);
  color: var(--color-info);
}

.method-indicator.delete {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.folder-icon {
  color: var(--color-warning);
  font-size: 16px;
}

.node-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-badge {
  font-size: 10px;
  margin-left: 4px;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.15s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px;
}

.case-list-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
  overflow: hidden;
}

.case-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.case-list-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.select-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-tertiary);
  text-align: center;
}

.select-hint h3 {
  margin: 16px 0 8px;
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-tertiary);
}

.select-hint p {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.selected-request-info {
  background: #fff;
  border-radius: 2px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
  min-width: 70px;
}

.info-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.info-value.url {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  color: var(--color-primary);
}

.cases-table-wrapper {
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.cases-table-wrapper :deep(.el-table) {
  border: none;
}

.cases-table-wrapper :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.cases-table-wrapper :deep(.el-table__row) {
  font-size: 13px;
}

.cases-table-wrapper :deep(.el-table .cell) {
  padding: 8px;
}

.cases-table-wrapper :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-border-secondary);
}

.case-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-name-text {
  font-weight: 500;
  color: var(--color-text-primary);
}

.params-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.response-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-tag {
  flex-shrink: 0;
}

.response-body {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-data-text {
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.request-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.request-name-text {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.no-cases {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  color: var(--color-text-tertiary);
}

.no-cases p {
  margin: 16px 0;
  font-size: 14px;
}

.method-tag,
.method-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 2px;
  text-transform: uppercase;
  min-width: 50px;
  text-align: center;
}

.method-tag.get,
.method-badge.get {
  background: var(--color-success-light);
  color: var(--color-success);
}

.method-tag.post,
.method-badge.post {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.method-tag.put,
.method-badge.put {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.method-tag.patch,
.method-badge.patch {
  background: var(--color-info-light);
  color: var(--color-info);
}

.method-tag.delete,
.method-badge.delete {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.editor-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: calc(90vh - 120px);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.request-name-input {
  width: 200px;
}

.request-name-input :deep(.el-input__wrapper),
.case-name-input :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
  border-bottom: 1px dashed var(--color-border-primary);
  border-radius: 0;
}

.request-name-input :deep(.el-input__wrapper:hover),
.case-name-input :deep(.el-input__wrapper:hover) {
  border-bottom-color: var(--color-primary);
}

.request-name-input :deep(.el-input__wrapper.is-focus),
.case-name-input :deep(.el-input__wrapper.is-focus) {
  border-bottom-style: solid;
}

.case-separator {
  color: var(--color-text-tertiary);
  margin: 0 4px;
}

.case-name-input {
  width: 150px;
}

.dialog-actions {
  display: flex;
  gap: 8px;
}

.editor-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.url-bar {
  display: flex;
  padding: 12px 16px;
  gap: 8px;
  border-bottom: 1px solid var(--color-border-primary);
}

.method-select {
  width: 100px;
}

.method-select :deep(.el-input__wrapper) {
  border-radius: 2px 0 0 4px;
}

.method-select.get :deep(.el-input__wrapper) {
  background: var(--color-success-light);
}

.method-select.get :deep(.el-input__inner) {
  color: var(--color-success);
  font-weight: 600;
}

.method-select.post :deep(.el-input__wrapper) {
  background: var(--color-primary-light);
}

.method-select.post :deep(.el-input__inner) {
  color: var(--color-primary);
  font-weight: 600;
}

.method-select.put :deep(.el-input__wrapper) {
  background: var(--color-warning-light);
}

.method-select.put :deep(.el-input__inner) {
  color: var(--color-warning);
  font-weight: 600;
}

.method-select.patch :deep(.el-input__wrapper) {
  background: var(--color-info-light);
}

.method-select.patch :deep(.el-input__inner) {
  color: var(--color-info);
  font-weight: 600;
}

.method-select.delete :deep(.el-input__wrapper) {
  background: var(--color-danger-light);
}

.method-select.delete :deep(.el-input__inner) {
  color: var(--color-danger);
  font-weight: 600;
}

.url-input {
  flex: 1;
}

.url-input :deep(.el-input__wrapper) {
  border-radius: 0 4px 4px 0;
}

.suffix-icon {
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.suffix-icon:hover {
  color: var(--color-primary);
}

.editor-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.config-section {
  border-bottom: 1px solid var(--color-border-primary);
}

.section-tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.section-tab {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.section-tab:hover {
  color: var(--color-primary);
}

.section-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-badge {
  margin-left: 2px;
}

.section-content {
  max-height: 200px;
  overflow: auto;
}

.config-form {
  padding: 12px 16px;
}

.form-option {
  margin-bottom: 8px;
}

.kv-table {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.kv-header {
  display: flex;
  background: var(--color-bg-secondary);
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-primary);
}

.kv-body {
  max-height: 150px;
  overflow: auto;
}

.kv-row {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.kv-row:last-child {
  border-bottom: none;
}

.kv-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  color: var(--color-text-tertiary);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
}

.kv-footer:hover {
  color: var(--color-primary);
}

.col-check {
  width: 24px;
}

.col-key {
  width: 160px;
  padding: 0 8px;
}

.col-value {
  width: 160px;
  padding: 0 8px;
}

.col-desc {
  flex: 1;
  padding: 0 8px;
}

.col-type {
  width: 80px;
}

.col-action {
  width: 32px;
}

.kv-row :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
}

.kv-row :deep(.el-input__inner) {
  font-size: 13px;
}

.body-type-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.raw-type {
  width: 100px;
}

.empty-body {
  padding: 32px;
  text-align: center;
  color: var(--color-text-tertiary);
}

.raw-editor {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.raw-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  border: none;
  resize: none;
}

.auth-config {
  max-width: 500px;
}

.auth-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.auth-label {
  width: 80px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.auth-select {
  width: 200px;
}

.auth-fields {
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.auth-field {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.auth-field:last-child {
  margin-bottom: 0;
}

.field-name {
  width: 80px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.assertion-config {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.assertion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.assertion-list {
  padding: 8px;
}

.assertion-item {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.assertion-item:last-child {
  margin-bottom: 0;
}

.assertion-type {
  width: 100px;
}

.assertion-op {
  width: 80px;
}

.assertion-target {
  width: 120px;
}

.assertion-expected{
  flex: 1;
}

.empty-assertion {
  padding: 20px;
  text-align: center;
  color: var(--color-text-tertiary);
}

.script-config {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.script-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  border: none;
  resize: none;
}

.response-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.response-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-item {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.meta-placeholder {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.response-tabs {
  display: flex;
}

.response-tab {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
}

.response-tab:hover {
  color: var(--color-primary);
}

.response-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.response-content {
  flex: 1;
  overflow: auto;
}

.response-body-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.body-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.format-select {
  width: 100px;
}

.body-content {
  flex: 1;
  overflow: auto;
}

.response-code {
  margin: 0;
  padding: 12px 16px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: var(--color-bg-secondary);
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.empty-response {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: var(--color-text-tertiary);
}

.response-headers-panel,
.response-cookies-panel,
.response-tests-panel,
.response-assertion-panel {
  padding: 12px 16px;
}

.headers-list,
.cookies-list,
.tests-list,
.assertion-results {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.header-item,
.cookie-item {
  display: flex;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.header-item:last-child,
.cookie-item:last-child {
  border-bottom: none;
}

.header-key,
.cookie-key {
  width: 180px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: var(--color-primary);
}

.header-value,
.cookie-value {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: var(--color-danger);
}

.test-item,
.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.test-item:last-child,
.result-item:last-child {
  border-bottom: none;
}

.test-item.passed,
.result-item.passed {
  background: var(--color-success-light);
}

.test-item.failed,
.result-item.failed{
  background: var(--color-danger-light);
}

.test-name,
.result-message {
  font-size: 13px;
  color: var(--color-text-primary);
}

.result-detail {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.title-count {
  color: var(--color-text-tertiary);
  font-size: 12px;
  background: var(--color-bg-tertiary);
  padding: 2px 8px;
  border-radius: 2px;
  font-weight: 500;
}

.batch-operation-wrapper {
  position: relative;
  display: inline-block;
}

.batch-active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.batch-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 140px;
  padding: 6px 0;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border: 1px solid var(--color-bg-tertiary);
  z-index: 1000;
}

.batch-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #333;
  font-size: 14px;
}

.batch-menu-item:hover {
  background: var(--color-bg-secondary);
}

.batch-menu-item.disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.batch-menu-item.disabled:hover {
  background: transparent;
}

.batch-menu-item.danger {
  color: var(--color-danger);
}

.batch-menu-item.danger:hover {
  background: var(--color-danger-light);
}

.batch-menu-item.danger.disabled {
  color: var(--color-danger);
}

.batch-menu-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--color-bg-tertiary);
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: all 0.2s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.batch-info {
  padding: 8px 20px;
  background: var(--color-primary-light);
  border-bottom: 1px solid var(--color-primary-light);
}

.batch-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-primary);
}

.batch-hint strong {
  color: var(--color-primary);
}
</style>
