# Thanks to Miguel Grinberg
# https://blog.miguelgrinberg.com/post/using-celery-with-flask
import random
import time

from flask import Flask, jsonify, url_for, request, render_template

from celery_app import celery_init_app


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

app.config.from_mapping(
    CELERY=dict(
        broker_url='amqp://guest:guest@localhost:5672//',
        result_backend='redis://localhost:6379/0',
        task_ignore_result=True,
    ),
)
celery_app = celery_init_app(app)


@celery_app.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)

    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb), random.choice(adjective), random.choice(noun))

        self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': message})

        time.sleep(1)

    return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': 42}


@app.route('/longtask', methods=['POST'])
def longtask():
    task = long_task\
        .apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
