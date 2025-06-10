import flask
import public_navigation.final as pn  # your module that does the real stuff
import requests
import threading
import json
import time

app = flask.Flask(__name__)

TIME_TABLES = {}    # train_id: list[str]
DESTINATIONS = {}   # train_id: str
AT = {}           # train_id: int
DEBUG_POSITION = {}  # train_id: str
TRAINS= [0] # list of train IDs eg 0 1 2 etc
data_lock = threading.Lock()



def do_after_arrival(train_id, waittime):
    time.sleep(waittime)
    with data_lock:
        if waittime != 0:
            AT[train_id] += 1
            if AT[train_id] >= len(TIME_TABLES[train_id]):
                AT[train_id] = 0
        DESTINATIONS[train_id] = TIME_TABLES[train_id][AT[train_id]]
        print(f"[AFTER] {waittime}s passed since {train_id} arrived we go to {TIME_TABLES[train_id][AT[train_id]]}")
        requests.post(f"http://127.0.0.1:5080/set_plan/{train_id}", data=TIME_TABLES[train_id][AT[train_id]])  # or maybe do something else



def main_loop():
    while True:
        try:
            position=requests.get("http://127.0.0.1:5080/get_positions").json()
        except:
            time.sleep(5)
            continue
        with data_lock:
            #position = DEBUG_POSITION.copy()
            TRAINS=list(position.keys())
            for train_id, pos in TIME_TABLES.items():
                if list(position.values())[int(train_id)] == DESTINATIONS[train_id]:
                    print(f"{train_id} arrived at {list(position.values())[int(train_id)]}")
                    AT[train_id] += 1
                    if AT[train_id] >= len(TIME_TABLES[train_id]):
                        AT[train_id] = 0
                    if isinstance(TIME_TABLES[train_id][AT[train_id]], int):
                        waittime= TIME_TABLES[train_id][AT[train_id]]
                    else:
                        waittime= 0
                        #print(f"Waiting for {waittime} seconds")
            
                    t = threading.Thread(target=do_after_arrival, args=(train_id, waittime), daemon=True)
                    t.start()

                    DESTINATIONS[train_id] =False
                
        time.sleep(1)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response 

@app.route("/trains", methods=["GET"])
def get_trains():
    with data_lock:
        return flask.jsonify({
            "time_tables": TIME_TABLES,
            "step": AT,
            "trains": TRAINS
        })

@app.route("/debug_setpos", methods=["POST"])
def debug_setpos():
    global DEBUG_POSITION
    with data_lock:
        data = flask.request.json
        DEBUG_POSITION=data.copy()
        print(f"Debug position set: {DEBUG_POSITION}")
    return flask.jsonify({"message": "Position updated successfully"})

@app.route("/set_plan/<train_id>", methods=["POST"])
def set_plan(train_id):
    data = flask.request.get_data(as_text=True)
    print(f"Server received: {data}")
    with data_lock:
        DESTINATIONS[train_id] = json.loads(data)[0]
        AT[train_id] = 0
        TIME_TABLES[train_id] = json.loads(data)
        print(f"Plan set for train {train_id}: {TIME_TABLES[train_id]}")
        
    return flask.jsonify({"message": "Plan set successfully"})

@app.route("/", methods=["GET"])
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Train Control Frontend</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.14.0/Sortable.min.js"></script>
    <style>
        .train-container {
            width: 300px;
            margin: 10px;
            padding: 10px;
            border: 1px solid #ccc;
            display: flex;
            flex-direction: column;
            background-color: #fff;
        }
        .train-container.unsaved {
            border: 2px solid orange;
        }
        .schedule-list {
            list-style: none;
            padding: 0;
            min-height: 20px;
        }
        .schedule-list li {
            padding: 5px;
            margin: 2px 0;
            background-color: #f0f0f0;
            cursor: move;
            position: relative;
        }
        .schedule-list li.current-step {
            background-color: #ffff99;
        }
        .schedule-list li button {
            position: absolute;
            right: 5px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: red;
            cursor: pointer;
            font-size: 14px;
        }
        .add-item {
            margin-top: 10px;
            display: flex;
            align-items: center;
        }
        .add-item select, .add-item input {
            margin-right: 5px;
        }
        button {
            margin-top: 5px;
            padding: 5px 10px;
            cursor: pointer;
        }
        button:hover {
            background-color: #e0e0e0;
        }
    </style>
</head>
<body>
    <div id="trains" style="display: flex; flex-wrap: wrap;"></div>
    <script>
        function buildTrainContainer(trainId, schedule, step) {
            const container = document.createElement('div');
            container.className = 'train-container';
            container.dataset.trainId = trainId;

            const header = document.createElement('h2');
            header.textContent = `Train ${trainId}`;
            container.appendChild(header);

            const scheduleList = document.createElement('ul');
            scheduleList.className = 'schedule-list';
            if (schedule && schedule.length > 0) {
                schedule.forEach((item, index) => {
                    const li = document.createElement('li');
                    if (typeof item === 'string') {
                        li.dataset.type = 'station';
                        li.dataset.value = item;
                        li.textContent = `Station: ${item}`;
                    } else {
                        li.dataset.type = 'wait';
                        li.dataset.value = item;
                        li.textContent = `Wait: ${item} min`;
                    }
                    if (index === step) {
                        li.classList.add('current-step');
                    }
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'x';
                    deleteButton.addEventListener('click', () => {
                        li.remove();
                        container.classList.add('unsaved');
                    });
                    li.appendChild(deleteButton);
                    scheduleList.appendChild(li);
                });
            }
            container.appendChild(scheduleList);

            new Sortable(scheduleList, {
                animation: 150,
                onEnd: () => {
                    container.classList.add('unsaved');
                }
            });

            const addItemDiv = document.createElement('div');
            addItemDiv.className = 'add-item';

            const typeSelect = document.createElement('select');
            typeSelect.className = 'type-select';
            typeSelect.innerHTML = `
                <option value="station">Station</option>
                <option value="wait">Wait Time</option>
            `;

            const stationInput = document.createElement('input');
            stationInput.type = 'text';
            stationInput.className = 'station-input';
            stationInput.placeholder = 'Station name';

            const waitInput = document.createElement('input');
            waitInput.type = 'number';
            waitInput.className = 'wait-input';
            waitInput.placeholder = 'Wait time in minutes';
            waitInput.style.display = 'none';

            const addButton = document.createElement('button');
            addButton.className = 'add-button';
            addButton.textContent = 'Add';

            addItemDiv.appendChild(typeSelect);
            addItemDiv.appendChild(stationInput);
            addItemDiv.appendChild(waitInput);
            addItemDiv.appendChild(addButton);
            container.appendChild(addItemDiv);

            typeSelect.addEventListener('change', () => {
                if (typeSelect.value === 'station') {
                    stationInput.style.display = 'block';
                    waitInput.style.display = 'none';
                } else {
                    stationInput.style.display = 'none';
                    waitInput.style.display = 'block';
                }
            });

            addButton.addEventListener('click', () => {
                const type = typeSelect.value;
                let value;
                if (type === 'station') {
                    value = stationInput.value.trim();
                    if (!value) return;
                } else {
                    value = waitInput.value.trim();
                    if (!value || isNaN(value)) return;
                    value = parseInt(value, 10);
                }
                const li = document.createElement('li');
                li.dataset.type = type;
                li.dataset.value = value;
                li.textContent = type === 'station' ? `Station: ${value}` : `Wait: ${value} min`;
                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'x';
                deleteButton.addEventListener('click', () => {
                    li.remove();
                    container.classList.add('unsaved');
                });
                li.appendChild(deleteButton);
                scheduleList.appendChild(li);
                stationInput.value = '';
                waitInput.value = '';
                container.classList.add('unsaved');
            });

            const updateButton = document.createElement('button');
            updateButton.className = 'update-button';
            updateButton.textContent = 'Update';
            updateButton.addEventListener('click', () => {
                const items = scheduleList.querySelectorAll('li');
                const updatedSchedule = [];
                items.forEach(item => {
                    const type = item.dataset.type;
                    const value = item.dataset.value;
                    if (type === 'station') {
                        updatedSchedule.push(value);
                    } else {
                        updatedSchedule.push(parseInt(value, 10));
                    }
                });
                fetch(`/set_plan/${trainId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedSchedule),
                }).then(response => {
                    if (response.ok) {
                        console.log(`Schedule for Train ${trainId} updated`);
                        rebuildTrainContainer(trainId);
                    } else {
                        console.error('Failed to update schedule');
                    }
                }).catch(error => console.error('Error:', error));
            });
            container.appendChild(updateButton);

            const resetButton = document.createElement('button');
            resetButton.className = 'reset-button';
            resetButton.textContent = 'Reset';
            resetButton.addEventListener('click', () => rebuildTrainContainer(trainId));
            container.appendChild(resetButton);

            return container;
        }

        function fetchTrains(fullRebuild = false) {
            fetch('/trains')
                .then(response => response.json())
                .then(data => {
                    const trainsDiv = document.getElementById('trains');
                    if (fullRebuild) {
                        trainsDiv.innerHTML = '';
                        data.trains.forEach(trainId => {
                            const schedule = data.time_tables[trainId] || [];
                            const step = data.step[trainId] !== undefined ? data.step[trainId] : -1;
                            const container = buildTrainContainer(trainId, schedule, step);
                            trainsDiv.appendChild(container);
                        });
                    } else {
                        const existingContainers = Array.from(trainsDiv.querySelectorAll('.train-container'));
                        const serverTrainIds = data.trains;

                        // Update or add trains
                        serverTrainIds.forEach(trainId => {
                            const step = data.step[trainId] !== undefined ? data.step[trainId] : -1;
                            const container = existingContainers.find(c => c.dataset.trainId === trainId);
                            if (container) {
                                // Only update the current step highlight
                                const scheduleList = container.querySelector('.schedule-list');
                                const items = scheduleList.querySelectorAll('li');
                                items.forEach(item => item.classList.remove('current-step'));
                                if (step >= 0 && step < items.length) {
                                    items[step].classList.add('current-step');
                                }
                            } else {
                                // Add new train
                                const schedule = data.time_tables[trainId] || [];
                                const newContainer = buildTrainContainer(trainId, schedule, step);
                                trainsDiv.appendChild(newContainer);
                            }
                        });

                        // Remove trains no longer present
                        existingContainers.forEach(container => {
                            if (!serverTrainIds.includes(container.dataset.trainId)) {
                                container.remove();
                            }
                        });
                    }
                })
                .catch(error => console.error('Error fetching trains:', error));
        }

        function rebuildTrainContainer(trainId) {
            fetch('/trains')
                .then(response => response.json())
                .then(data => {
                    const schedule = data.time_tables[trainId] || [];
                    const step = data.step[trainId] !== undefined ? data.step[trainId] : -1;
                    const newContainer = buildTrainContainer(trainId, schedule, step);
                    const oldContainer = document.querySelector(`.train-container[data-train-id="${trainId}"]`);
                    if (oldContainer) {
                        oldContainer.replaceWith(newContainer);
                    } else {
                        document.getElementById('trains').appendChild(newContainer);
                    }
                })
                .catch(error => console.error('Error rebuilding train:', error));
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchTrains(true); // Initial full build
            setInterval(() => fetchTrains(false), 5000); // Periodic step updates
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    app.run(port=9998, host="0.0.0.0")
