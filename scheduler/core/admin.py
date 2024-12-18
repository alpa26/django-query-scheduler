from django.contrib import admin
from .models import Task, TaskResult
from django.utils.html import format_html


class TaskResultInline(admin.TabularInline):
    """
        Класс для отображения результатов задач в админке Django в виде таблицы.
    """
    model = TaskResult
    extra = 1


class TaskAdmin(admin.ModelAdmin):
    """
        Класс для настройки административного интерфейса для модели Task.

        Параметры:
            list_display - Список полей, которые будут отображаться в таблице списка задач.
            list_filter - Список полей, по которым можно фильтровать задачи.
            search_fields - Список полей, по которым можно выполнять поиск.
            inlines - Список встроенных классов для отображения связанных моделей.
    """
    list_display = ('name', 'resource', 'task_type', 'schedule_time',
                    'repeat_interval', 'next_run', 'is_active',
                    'start_task_button')
    list_filter = ('task_type', 'repeat_interval', 'is_active')
    search_fields = ('name', 'resource')
    inlines = [TaskResultInline]

    def start_task_button(self, obj):
        """
            Метод для отображения кнопки запуска задачи в таблице списка задач.
        """
        return format_html(
            '<button class="start-task-button"\
             data-task-id="{}">Запуск задачи</button>',
            obj.pk
        )

    start_task_button.short_description = 'Запуск задачи'

    class Media:
        """
            Класс для подключения медиафайлов JavaScript в админке.
        """
        js = ('admin/js/start_task.js',)


class TaskResultAdmin(admin.ModelAdmin):
    """
        Класс для настройки административного интерфейса для модели TaskResult.

        Параметры:
            list_display - Список полей, которые будут отображаться в таблице списка задач.
            list_filter - Список полей, по которым можно фильтровать задачи.
            search_fields - Список полей, по которым можно выполнять поиск.
    """

    list_display = ('task', 'status', 'timestamp')
    list_filter = ('status',)
    search_fields = ('task__name', 'status')


admin.site.register(Task, TaskAdmin)
admin.site.register(TaskResult, TaskResultAdmin)
