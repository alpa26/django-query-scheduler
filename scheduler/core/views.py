from django.http import HttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Task, TaskResult
from .serializers import TaskSerializer, TaskResultSerializer
from .dramatiq_tasks import run_api_task, run_db_task
from django.utils import timezone
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


def index(request):
    """Метод отображения начальной страницы"""
    return HttpResponse("Добро пожаловать")


def start_task(task_id):
    """
        Метод для одноразового запуска задачи

        Описание:
            1. Пытается найти задачу по task_id
            2. В зависимости от типа задачи вызывает методы фонового выполнения задач
             аргументом attempt = -1
            3. При возниконовении исключений бросает ошибку
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Задача не создана"},
                        status=status.HTTP_404_NOT_FOUND)

    if task.task_type == 'api':
        run_api_task.send(task.id, -1)
        print("api one time")
    elif task.task_type == 'db':
        run_db_task.send(task.id, -1)
        print("api one time")
    else:
        return Response({"error": "Неправильный тип задачи"},
                        status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Задача успешно запустилась"},
                    status=status.HTTP_200_OK)


@api_view(['POST'])
def start_task_view(request, task_id):
    """
        Метод API для одноразового запуска задачи.
        Вызывает метод start_task, если результат выполнения не 200 аозвращает ошибку
    """
    response = start_task(task_id)
    if response.status_code == 200:
        return Response({"message": "Task started successfully"},
                        status=status.HTTP_200_OK)
    return Response(response.data, status=response.status_code)


def handle_task_creation(task):
    """
        Метод для запуска задачи

        Описание:
            1. В зависимости от типа задачи вызывает методы фонового выполнения задач
             без аргументом attempt (по умолчанию attempt = 1).
            2. Планирует выполнение задачи с задержкой, если время выполнение еще не пройдено.
    """
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
    """
        ViewSet для управления задачами (Task).

        Параметры:
            queryset - Набор всех объектов модели.
            serializer_class - Класс сериализатора для модели.

        Методы:
            perform_create - Метод для выполнения создания новой задачи.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()


class TaskResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
       ViewSet для отображения результатов задач (TaskResult).

       Параметры:
           queryset - Набор всех объектов модели.
           serializer_class - Класс сериализатора для модели.

       Методы:
           get_queryset - Метод для получения результатов задач, фильтруемых по task_id.
    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        return TaskResult.objects.filter(task_id=task_id)

