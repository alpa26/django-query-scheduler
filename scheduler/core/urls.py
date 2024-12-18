from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskResultViewSet, start_task_view

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tasks/<int:task_id>/results/',
         TaskResultViewSet.as_view({'get': 'list'}),
         name='task-results'),
    path('tasks/start/<int:task_id>/', start_task_view, name='start-task')
]
