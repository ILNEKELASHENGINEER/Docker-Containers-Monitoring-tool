from flask import Flask, render_template, jsonify, request
import docker
import time

app = Flask(__name__)
client = docker.from_env()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/monitoring-data', methods=['GET'])
def get_monitoring_data():
    duration = request.args.get('duration', '24hr')
    data = collect_monitoring_data(duration)
    return jsonify(data)

def collect_monitoring_data(duration):
    end_time = time.time()
    start_time = end_time - parse_duration(duration)

    data = {
        'cpu_usage': [],
        'memory_usage': []
    }

    for container in client.containers.list():
        stats = container.stats(stream=False)
        timestamp = stats['read']
        cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
        memory_usage = stats['memory_stats']['usage']

        data['cpu_usage'].append({'timestamp': timestamp, 'container': container.name, 'cpu_usage': cpu_usage})
        data['memory_usage'].append({'timestamp': timestamp, 'container': container.name, 'memory_usage': memory_usage})

    return data

def parse_duration(duration):
    if duration == '30min':
        return 1800
    elif duration == '1hr':
        return 3600
    elif duration == '2hr':
        return 7200
    elif duration == '6hr':
        return 21600
    elif duration == '12hr':
        return 43200
    elif duration == '24hr':
        return 86400
    return 86400

if __name__ == '__main__':
    app.run(debug=True)
