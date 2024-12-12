from django.contrib import admin
from .models import Task, TaskResult

class TaskResultInline(admin.TabularInline):
    model = TaskResult
    extra = 1

class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource', 'task_type', 'schedule_time' ,'repeat_interval', 'next_run','is_active')
    list_filter = ('task_type', 'repeat_interval', 'is_active')
    search_fields = ('name', 'resource')
    inlines = [TaskResultInline]

class TaskResultAdmin(admin.ModelAdmin):
    list_display = ('task', 'status', 'timestamp')
    list_filter = ('status',)
    search_fields = ('task__name', 'status')

admin.site.register(Task, TaskAdmin)
admin.site.register(TaskResult, TaskResultAdmin)