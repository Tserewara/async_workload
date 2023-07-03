import json
from datetime import datetime
import time

from flask import Flask, render_template, Response, jsonify

from celery_app import celery_init_app

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config.task_serializer = 'json'

app.config.from_mapping(
    CELERY=dict(
        broker_url='amqp://guest:guest@localhost:5672//',
        result_backend='redis://localhost:6379/0',
        backend="rpc://",
        task_serializer='json'
    ),
)
celery_app = celery_init_app(app)


@celery_app.task(bind=True)
def process_name(self, name, birthdate):
    age = calculate_age(birthdate)
    time.sleep(10)  # Simulating a long-running task

    return {
        "name": name,
        "age": age
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/longtask', methods=['POST'])
def longtask():
    # return all the tasks id to create table
    names = [('Alice', '1990-05-15'), ('Bob', '1985-12-25'), ('Charlie', '1995-09-10')]
    task_ids = []
    for name, birthdate in names:
        task = process_name.apply_async([name, birthdate])
        task_ids.append(task.id)
    return jsonify(task_ids), 202


@app.route('/status/<string:task_id>')
def task_status(task_id):
    def generate(task_id):
        task = celery_app.AsyncResult(task_id)
        task_result = {
            "id": task_id,
            "status": "PENDING",
            "result": None
        }
        if task.status == "SUCCESS":
            task_result["status"] = task.status
            task_result["result"] = task.result
            yield f"data: {json.dumps(task_result)}\n\n"
        elif task.status == "PENDING":
            yield f"data: {json.dumps(task_result)}"
        elif task.status == "FAILURE":
            task_result["status"] = task.status

    return Response(generate(task_id), mimetype='text/event-stream')


def calculate_age(birthdate):
    birthdate = datetime.strptime(birthdate, '%Y-%m-%d').date()
    today = datetime.now().date()
    age = today.year - birthdate.year

    # Check if the birthday has already occurred this year
    if today.month < birthdate.month or (today.month == birthdate.month and today.day < birthdate.day):
        age -= 1

    return age


if __name__ == '__main__':
    app.run(debug=True)
