# Commands

- Run rabbitmq and redis with docker compose
```shell
 docker compose up -d
```

- Run celery worker (intentionally run manually)
```shell
celery -A app.celery_app worker --loglevel=INFO
```

- Run flower to inspect celery
```shell
celery -A app.celery_app flower
```
