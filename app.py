import csv
import json
from datetime import datetime
import time

from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
import redis

from celery_app import celery_init_app

app = Flask(__name__)

redis_db = redis.Redis(host='localhost', port=6379, db=1)

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


@app.route('/upload', methods=['POST'])
def upload_csv():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return 'No file uploaded.', 400

    # Get the uploaded file
    file = request.files['file']

    # Check if the file has a valid extension
    if not file.filename.endswith('.csv'):
        return 'Invalid file extension. Please upload a CSV file.', 400

    # Read the CSV file
    try:
        csv_data = file.read().decode('utf-8')
        csv_rows = csv_data.splitlines()
        csv_reader = csv.reader(csv_rows)
    except Exception as e:
        return 'Error reading the CSV file: {}'.format(str(e)), 400

    # Process the CSV data and add to Redis
    try:
        for row in csv_reader:
            # Assuming the CSV structure is 'id, name, birthdate'
            if len(row) != 3:
                return 'Invalid CSV structure. Expected 3 columns: id, name, birthdate.', 400

            # Process the row data
            id, name, birthdate = row
            # Here you can perform any operations or validations on the data
            # For example, you can store it in a database or perform some calculations

            # Add the data to Redis
            redis_db.hset('csv_data', id, f'{name},{birthdate}')

    except Exception as e:
        return 'Error adding data to Redis: {}'.format(str(e)), 500

    # Return a success message
    return redirect(url_for('index'))


@app.route('/process_spreadsheet', methods=['POST'])
def process_spreadsheet():
    task_ids = []
    data = {}
    all_keys = redis_db.hkeys('csv_data')
    for key in all_keys:
        value = redis_db.hget('csv_data', key).decode('utf-8')
        name, birthdate = value.split(',')
        data[key.decode('utf-8')] = {
            'name': name,
            'birthdate': birthdate
        }
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
