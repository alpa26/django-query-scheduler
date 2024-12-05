import os

import dramatiq
import requests
from django.utils import timezone
from .models import Task, TaskResult
import sqlite3


@dramatiq.actor
def run_api_task(task_id,attempt=1):
    task = Task.objects.get(id=task_id)
    print("found api")
    try:
        response = requests.get(task.request)
        response.raise_for_status()
        result = response.text
        status = 'success'
        task.last_run = timezone.now()
        task.save()
        TaskResult.objects.create(task=task, result=result, status=status)
        if task.repeat_interval == 'hourly':
            task.next_run = task.last_run + timezone.timedelta(days=1)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_api_task.send_with_options(args=(task_id,), delay=int(delay))
        if task.repeat_interval == 'daily':
            task.next_run = task.last_run + timezone.timedelta(days=1)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_api_task.send_with_options(args=(task_id,), delay=int(delay))
        if task.repeat_interval == 'weekly':
            task.next_run = task.last_run + timezone.timedelta(days=7)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_api_task.send_with_options(args=(task_id,), delay=int(delay))

    except requests.exceptions.RequestException as e:
        result = str(e)
        status = 'error'
        if (attempt != 5):
            TaskResult.objects.create(task=task, result=result, status=status)
            run_api_task.send_with_options(args=(task_id,attempt+1,), delay=10000)

@dramatiq.actor
def run_db_task(task_id,attempt=1):
    task = Task.objects.get(id=task_id)
    print("found")
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'db', task.resource)
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
        TaskResult.objects.create(task=task, result=result, status=status)
        if task.repeat_interval == 'hourly':
            task.next_run = task.last_run + timezone.timedelta(hours=1)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_db_task.send_with_options(args=(task_id,), delay=int(delay))
        if task.repeat_interval == 'daily':
            task.next_run = task.last_run + timezone.timedelta(days=1)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_db_task.send_with_options(args=(task_id,), delay=int(delay))
        if task.repeat_interval == 'weekly':
            task.next_run = task.last_run + timezone.timedelta(days=1)
            delay = (task.next_run - timezone.now()).total_seconds() * 1000
            run_db_task.send_with_options(args=(task_id,), delay=int(delay))
    except Exception as e:
        result = str(e)
        status = 'error'
        if(attempt != 5):
            TaskResult.objects.create(task=task, result=result, status=status)
            run_db_task.send_with_options(args=(task_id,attempt+1,), delay=300000)