from app.tasks import celery,test_webhook_task

if __name__ == "__main__":
    celery.worker_main()
