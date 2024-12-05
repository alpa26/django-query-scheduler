from django.http import HttpResponse
from rest_framework import viewsets, mixins
from .models import Task, TaskResult
from .serializers import TaskSerializer, TaskResultSerializer
from .tasks import run_api_task, run_db_task
from django.utils import timezone
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def index(request):
    return HttpResponse("Добро пожаловать")

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()
        print("action")
        if task.schedule_time <= timezone.now():
            if task.task_type == 'api':
                run_api_task.send(task.id)
                print("action")
            elif task.task_type == 'db':
                run_db_task.send(task.id)
                print("action")
        else:
            delay = (task.schedule_time - timezone.now()).total_seconds() * 1000
            if task.task_type == 'api':
                run_api_task.send_with_options(args=(task.id,), delay=int(delay))
            elif task.task_type == 'db':
                run_db_task.send_with_options(args=(task.id,), delay=int(delay))

class TaskResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        return TaskResult.objects.filter(task_id=task_id)

def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'core/task_list.html', {'tasks': tasks})

def hello_world(request):
    return render(request, 'core/hello_world.html')