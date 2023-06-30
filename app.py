import json
from datetime import datetime
import time

from flask import Flask, render_template, Response

app = Flask(__name__)


# app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
#
# app.config.from_mapping(
#     CELERY=dict(
#         broker_url='amqp://guest:guest@localhost:5672//',
#         result_backend='redis://localhost:6379/0',
#         task_ignore_result=True,
#     ),
# )
# celery_app = celery_init_app(app)


def process_names(names):
    for name, birthdate in names:
        age = calculate_age(birthdate)
        yield {
            "name": name,
            "age": age
        }
        time.sleep(3)  # Simulating a long-running task


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/update_table')
def update_table():
    names = [('Alice', '1990-05-15'), ('Bob', '1985-12-25'), ('Charlie', '1995-09-10')]

    def generate():
        for row in process_names(names):
            yield f"data: {json.dumps(row)}\n\n"
        yield "data: finished\n\n"

    return Response(generate(), mimetype='text/event-stream')


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
