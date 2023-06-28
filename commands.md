# Commands

- Create rabbitmq container
```shell
 docker run -d -p 5672:5672 rabbitmq
```

- Run celery worker
```shell
celery -A tasks worker --loglevel=INFO
```

- Inside the Python repl, run a task
```python
from tasks import add
add.delay(4, 4)
```

- Inside the Python repl, check if a task is  done
```python
from tasks import add
result = add.delay(4, 4)
result.get()
# 8
```