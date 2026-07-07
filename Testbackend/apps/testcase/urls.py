from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.viewsets import (
    TestCaseRepositoryViewSet,
    TestCaseVersionViewSet,
    TestModuleViewSet,
    TestCaseViewSet,
    TestCaseReviewViewSet,
    TestCaseExecutionViewSet
)
from .views.ai_views import (
    generate_test_cases_batch,
    generate_test_cases_stream_native,
    ai_service_status,
    cancel_ai_generation,
)

# ==================== DRF Router 配置 ====================
# 使用 DefaultRouter 自动生成 RESTful 路由
# 每个 ViewSet 会自动生成以下路由：
# - GET    /{resource}/          -> list (获取列表)
# - POST   /{resource}/          -> create (创建)
# - GET    /{resource}/{id}/     -> retrieve (获取详情)
# - PUT    /{resource}/{id}/     -> update (完整更新)
# - PATCH  /{resource}/{id}/     -> partial_update (部分更新)
# - DELETE /{resource}/{id}/     -> destroy (删除)

router = DefaultRouter()

# ==================== 用例库管理 ====================
# 路由前缀: /api/testcase/repositories/
# 功能: 管理测试用例库，每个项目可以有多个用例库
router.register(r'repositories', TestCaseRepositoryViewSet, basename='repository')

# ==================== 版本管理 ====================
# 路由前缀: /api/testcase/versions/
# 功能: 管理用例库的版本，每个用例库可以有多个版本
router.register(r'versions', TestCaseVersionViewSet, basename='version')

# ==================== 模块管理 ====================
# 路由前缀: /api/testcase/modules/
# 功能: 管理测试用例的模块树结构
# 自定义接口:
#   - GET /modules/tree/           -> 获取模块树
#   - GET /modules/statistics/     -> 获取模块统计信息
router.register(r'modules', TestModuleViewSet, basename='module')

# ==================== 测试用例管理 ====================
# 路由前缀: /api/testcase/cases/
# 功能: 管理测试用例
# 自定义接口:
#   - GET  /cases/by_version/      -> 根据版本获取用例
#   - GET  /cases/by_module/       -> 根据模块获取用例
#   - GET  /cases/by_module_tree/  -> 根据模块树获取用例（含子模块）
#   - GET  /cases/by_project/      -> 根据项目获取用例
#   - POST /cases/batch_copy/      -> 批量复制用例
#   - POST /cases/batch_delete/    -> 批量删除用例
#   - POST /cases/batch_move/      -> 批量移动用例
#   - POST /cases/batch_update/    -> 批量更新用例
#   - POST /cases/{id}/copy/       -> 复制单个用例
router.register(r'cases', TestCaseViewSet, basename='case')

# ==================== 用例评审管理 ====================
# 路由前缀: /api/testcase/reviews/
# 功能: 管理测试用例的评审记录
router.register(r'reviews', TestCaseReviewViewSet, basename='review')

# ==================== 用例执行记录管理 ====================
# 路由前缀: /api/testcase/executions/
# 功能: 管理测试用例的执行记录
# 自定义接口:
#   - GET /executions/by_test_case/  -> 获取指定用例的执行历史
router.register(r'executions', TestCaseExecutionViewSet, basename='execution')

urlpatterns = [
    path('', include(router.urls)),

    # AI生成接口
    path('ai/generate-batch/', generate_test_cases_batch, name='ai-generate-batch'),
    path('ai/generate-stream/', generate_test_cases_stream_native, name='ai-generate-stream'),
    path('ai/status/', ai_service_status, name='ai-status'),
    path('ai/cancel/', cancel_ai_generation, name='ai-cancel'),
]
