# Commands

- Run rabbitmq and redis with docker compose
```shell
 docker compose up -d
```

- Run celery worker (intentionally run manually)
```shell
celery -A main.celery_app worker --loglevel=INFO
```
