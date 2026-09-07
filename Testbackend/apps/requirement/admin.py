from django.contrib import admin
from apps.requirement.models import Requirement


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'func_point', 'priority', 'status', 'source', 'created_at']
    list_filter = ['priority', 'status', 'source']
    search_fields = ['title', 'func_point']
