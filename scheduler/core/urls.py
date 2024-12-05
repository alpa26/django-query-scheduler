from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskResultViewSet, task_list, hello_world

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tasks/<int:task_id>/results/', TaskResultViewSet.as_view({'get': 'list'}), name='task-results'),
    path('tasks/list/', task_list, name='task-list-view'),
    path('hello/', hello_world, name='hello-world'),
]