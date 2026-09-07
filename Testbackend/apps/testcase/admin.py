from django.contrib import admin
from apps.testcase.models import (
    TestCaseRepository,
    TestCaseVersion,
    TestModule,
    TestCase,
    TestCaseReview,
    TestCaseExecution
)


@admin.register(TestCaseRepository)
class TestCaseRepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'is_default', 'created_by', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['project', 'created_by']


@admin.register(TestCaseVersion)
class TestCaseVersionAdmin(admin.ModelAdmin):
    list_display = ['name', 'repository', 'status', 'is_default', 'created_at']
    list_filter = ['status', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['repository', 'created_by']


@admin.register(TestModule)
class TestModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'parent', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    raw_id_fields = ['version', 'parent']


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'module', 'version', 'priority',
        'automation_status', 'created_by', 'created_at'
    ]
    list_filter = ['priority', 'automation_status', 'created_at']
    search_fields = ['title', 'precondition', 'requirement__title', 'steps', 'expected_result']
    raw_id_fields = ['module', 'version', 'created_by', 'updated_by']


@admin.register(TestCaseReview)
class TestCaseReviewAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'reviewer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['comment']
    raw_id_fields = ['test_case', 'reviewer']


@admin.register(TestCaseExecution)
class TestCaseExecutionAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'executed_by', 'result', 'executed_at']
    list_filter = ['result', 'executed_at']
    search_fields = ['actual_result', 'remark']
    raw_id_fields = ['test_case', 'executed_by']
