from django.contrib import admin
from apps.projects.models import Project, ProjectMember, ProjectRole


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'type', 'status', 'owner', 'created_at']
    list_filter = ['type', 'status', 'visibility']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status']
    search_fields = ['user__username', 'project__name']
    readonly_fields = ['joined_at', 'updated_at']


@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    list_display = ['project', 'role_key', 'created_at']
    list_filter = ['role_key']
    search_fields = ['project__name']
    readonly_fields = ['created_at', 'updated_at']
