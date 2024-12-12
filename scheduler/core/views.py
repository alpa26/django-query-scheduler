from django.http import HttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Task, TaskResult
from .serializers import TaskSerializer, TaskResultSerializer
from .tasks import run_api_task, run_db_task
from django.utils import timezone
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def index(request):
    return HttpResponse("Добро пожаловать")

@api_view(['POST'])
def start_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    if task.task_type == 'api':
        run_api_task.send(task.id,-1)
        print("api one time")
    elif task.task_type == 'db':
        run_db_task.send(task.id,-1)
        print("api one time")
    else:
        return Response({"error": "Invalid task type"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Task started successfully"}, status=status.HTTP_200_OK)

def handle_task_creation(task):
    if task.schedule_time <= timezone.now():
        if task.task_type == 'api':
            run_api_task.send(task.id)
            print("api")
        elif task.task_type == 'db':
            run_db_task.send(task.id)
            print("db")
    else:
        delay = (task.schedule_time - timezone.now()).total_seconds() * 1000
        if task.task_type == 'api':
            run_api_task.send_with_options(args=(task.id,), delay=int(delay))
            print("api delay")
        elif task.task_type == 'db':
            run_db_task.send_with_options(args=(task.id,), delay=int(delay))
            print("db delay")

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()

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