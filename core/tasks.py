from celery import shared_task

@shared_task
def my_scheduled_task():
    print("Periyodik görev çalıştı.")