import os
import openpyxl
from openpyxl import Workbook
import dramatiq
import requests
from django.utils import timezone
from .models import Task, TaskResult
import sqlite3


def enter_data_in_table(task, response, status):
    """
        Метод для записи результатов в excel таблицу

        Описание:
            1. Проверяет наличие таблицы и если ее нет, создает с необходимыми столбцами
            2. Если записывает результат выполнения в таблицу
    """
    print("table method")
    directory = 'excel_tables'
    file_path = os.path.join(os.path.dirname(__file__),
                             '..', directory,
                             task.table_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        print(f"found table {file_path}")
    except FileNotFoundError:
        print(f"not found table {file_path}")
        workbook = Workbook()
        sheet = workbook.active
        headers = ["Name", "Type", "Resource",
                   "Request", "Status", "Responce",
                   "ScheduleTime"]
        sheet.append(headers)

    row = [
        task.name,
        task.task_type,
        task.resource,
        task.request,
        status,
        response,
        task.schedule_time.strftime('%Y-%m-%d %H:%M:%S')
    ]

    print(f"{task.name},{task.task_type},\
            {task.resource},{task.request},{response},\
            {task.schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
    sheet.append(row)
    workbook.save(file_path)


@dramatiq.actor
def run_api_task(task_id, attempt=1):
    """
        Метод для фонового выполнения задачи через обращение к стороннему сервису через API.

        Параметры:
        task_id - Идентификатор задачи, которую нужно выполнить.
        attempt - Номер попытки выполнения задачи. По умолчанию 1.

        Описание:
        1. Получает задачу по её идентификатору.
        2. Проверяет активность задачи. Если задача не активна, метод завершает выполнение.
        3. Отправляет API запрос к стороннему сервису по URL, указанному в задаче.
        4. Проверяет успешность ответа и сохраняет результат.
        5. Если задача имеет таблицу для записи данных, результат записывается в таблицу.
        6. Записывает результат выполнения задачи.
        7. Если задача должна повторяться, метод планирует следующее выполнение задачи.
        8  В случае ошибки, метод повторяет выполнение задачи до 3 раз с интервалом в 60 секунд.


        Примечаниe:
        - Если параметр `attempt` равен -1, задача выполняется только один раз.
    """
    task = Task.objects.get(id=task_id)
    if (not task.is_active):
        return
    print("found api")
    try:
        response = requests.get(task.request)
        response.raise_for_status()
        result = response.text
        status = 'success'
        task.last_run = timezone.now()
        task.save()
        if (task.table_name):
            enter_data_in_table(task, result, status)
        TaskResult.objects.create(task=task, result=result, status=status)
        # Если задача вызывается с параметром attempt == -1 то задача выполняется 1 раз
        if attempt != -1:
            if task.repeat_interval == 'hourly':
                task.next_run = task.last_run + timezone.timedelta(days=1)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_api_task.send_with_options(args=(task_id,),
                                               delay=int(delay))
                task.save()
            if task.repeat_interval == 'daily':
                task.next_run = task.last_run + timezone.timedelta(days=1)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_api_task.send_with_options(args=(task_id,),
                                               delay=int(delay))
                task.save()
            if task.repeat_interval == 'weekly':
                task.next_run = task.last_run + timezone.timedelta(days=7)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_api_task.send_with_options(args=(task_id,),
                                               delay=int(delay))
                task.save()

    except requests.exceptions.RequestException as e:
        if (attempt == -1):
            attempt = 1
        result = str(e)
        status = 'error'
        if (attempt < 4):
            TaskResult.objects.create(task=task, result=result, status=status)
            run_api_task.send_with_options(args=(task_id, attempt + 1,),
                                           delay=60000)


@dramatiq.actor
def run_db_task(task_id, attempt=1):
    """
        Метод для фонового выполнения задачи, связанной с базой данных SQLite.

        Параметры:
        task_id - Идентификатор задачи, которую нужно выполнить.
        attempt - Номер попытки выполнения задачи. По умолчанию 1.

        Описание:
        1. Получает задачу по её идентификатору.
        2. Проверяет активность задачи. Если задача не активна, метод завершает выполнение.
        3. Устанавливает соединение с базой данных и выполняет SQL-запрос, указанный в задаче
            Если база данных не существует, то создает ее.
        5. Если задача имеет таблицу для записи данных, результат записывается в таблицу.
        6. Записывает результат выполнения задачи.
        7. Если задача должна повторяться, метод планирует следующее выполнение задачи.
        8 В случае ошибки, метод повторяет выполнение задачи до 3 раз с интервалом в 60 секунд.

        Примечание:
        - Если параметр `attempt` равен -1, задача выполняется только один раз.
    """
    task = Task.objects.get(id=task_id)
    if (not task.is_active):
        return
    print("try")
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..',
                               'db', f"{task.resource}.sqlite3")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()
        cursor.execute(task.request)
        result = cursor.fetchall()

        conn.commit()
        conn.close()

        status = 'success'
        task.last_run = timezone.now()
        task.save()
        if isinstance(result, list):
            result_str = ', '.join(map(str, result))
        else:
            result_str = result
        if (task.table_name):
            enter_data_in_table(task, result_str, status)
        TaskResult.objects.create(task=task, result=result, status=status)
        # Если задача вызывается с параметром attempt == -1 то задача выполняется 1 раз
        if attempt != -1:
            if task.repeat_interval == 'hourly':
                task.next_run = task.last_run + timezone.timedelta(hours=1)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_db_task.send_with_options(args=(task_id,),
                                              delay=int(delay))
                task.save()
            if task.repeat_interval == 'daily':
                task.next_run = task.last_run + timezone.timedelta(days=1)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_db_task.send_with_options(args=(task_id,),
                                              delay=int(delay))
                task.save()
            if task.repeat_interval == 'weekly':
                task.next_run = task.last_run + timezone.timedelta(days=1)
                delay = (task.next_run - timezone.now()).total_seconds() * 1000
                run_db_task.send_with_options(args=(task_id,),
                                              delay=int(delay))
                task.save()
    except Exception as e:
        if (attempt == -1):
            attempt = 1
        result = str(e)
        status = 'error'
        if (attempt < 4):
            TaskResult.objects.create(task=task, result=result, status=status)
            run_db_task.send_with_options(args=(task_id, attempt + 1,),
                                          delay=60000)
