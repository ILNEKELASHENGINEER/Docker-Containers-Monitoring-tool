from flask import Flask, render_template_string, jsonify
import subprocess
import threading
import time
import re

app = Flask(__name__)
stats_data = []

def parse_docker_stats(output):
    lines = output.splitlines()
    container_stats = []
    
    for line in lines[1:]:  # Skip the header line
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 6:
            try:
                cpu_usage = float(parts[2].replace('%', '').strip())
            except ValueError:
                cpu_usage = 0
                
            try:
                mem_percent_str = parts[5].replace('%', '').strip()
                mem_percent = float(mem_percent_str)
            except ValueError:
                mem_percent = 0
            
            container_stats.append({
                'id': parts[0],
                'name': parts[1],
                'cpu': cpu_usage,
                'mem_percent': mem_percent
            })
    
    return container_stats

def update_stats():
    global stats_data
    while True:
        # Run `docker stats` command and capture the output
        result = subprocess.run(['docker', 'stats', '--no-stream'], capture_output=True, text=True)
        stats_data = parse_docker_stats(result.stdout)
        time.sleep(1)  # Update every 1 second

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="5">
            <title>Docker Stats Visualization</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 20px;
                }
                canvas {
                    display: inline-block;
                    margin: 10px;
                }
                .chart-container {
                    display: inline-block;
                    margin: 20px;
                }
                .caption {
                    font-size: 16px;
                    margin-top: 5px;
                }
            </style>
        </head>
        <body>
            <h1>Docker Stats Visualization</h1>
            <div id="charts">
                <!-- Dynamic content will be inserted here -->
            </div>

            <script>
                let cpuCharts = {};
                let memCharts = {};

                function createChart(id, label, data, max, unit) {
                    return new Chart(document.getElementById(id), {
                        type: 'bar',
                        data: {
                            labels: [label],
                            datasets: [{
                                label: label,
                                data: [data],
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                borderColor: 'rgba(75, 192, 192, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            plugins: {
                                datalabels: {
                                    display: true,
                                    formatter: function(value) {
                                        return value.toFixed(2) + unit;
                                    },
                                    color: '#000',
                                    anchor: 'end',
                                    align: 'top'
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: max
                                }
                            }
                        }
                    });
                }

                function updateCharts(data) {
                    const chartsDiv = document.getElementById('charts');
                    chartsDiv.innerHTML = ''; // Clear existing charts

                    data.forEach(container => {
                        const containerDiv = document.createElement('div');
                        containerDiv.className = 'chart-container';
                        containerDiv.innerHTML = `
                            <h3>${container.name}</h3>
                            <canvas id="cpu-${container.id}"></canvas>
                            <div class="caption">CPU Usage: ${container.cpu.toFixed(2)}%</div>
                            <canvas id="mem-${container.id}"></canvas>
                            <div class="caption">Memory Usage: ${container.mem_percent.toFixed(2)}%</div>
                        `;
                        chartsDiv.appendChild(containerDiv);

                        cpuCharts[container.id] = createChart(
                            `cpu-${container.id}`,
                            `CPU ${container.name}`,
                            container.cpu,
                            100,
                            '%'
                        );

                        memCharts[container.id] = createChart(
                            `mem-${container.id}`,
                            `Memory ${container.name}`,
                            container.mem_percent,
                            100,
                            '%'
                        );
                    });
                }

                function fetchData() {
                    fetch('/api/stats')
                        .then(response => response.json())
                        .then(data => {
                            updateCharts(data);
                        })
                        .catch(error => console.error('Error fetching data:', error));
                }

                // Fetch data and update every second
                setInterval(fetchData, 1000);
                
                // Initial fetch
                fetchData();
            </script>
        </body>
        </html>
    ''')

@app.route('/api/stats')
def api_stats():
    return jsonify(stats_data)

if __name__ == '__main__':
    # Start the background thread to update stats
    thread = threading.Thread(target=update_stats)
    thread.daemon = True
    thread.start()
    
    app.run(host='0.0.0.0', port=5555)
