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
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Train Control Frontend</title>
    <!-- Include SortableJS for drag-and-drop functionality -->
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

        .schedule-list {
            list-style: none;
            padding: 0;
            min-height: 20px; /* Ensures empty lists are visible for dragging */
        }

        .schedule-list li {
            padding: 5px;
            margin: 2px 0;
            background-color: #f0f0f0;
            cursor: move;
            position: relative;
        }

        .schedule-list li.current-step {
            background-color: #ffff99; /* Highlight for current step */
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
    <!-- Container for all train containers -->
    <div id="trains" style="display: flex; flex-wrap: wrap;"></div>
    <script>
        // Build a train container (assumed existing function, included for clarity)
function buildTrainContainer(trainId, schedule, step) {
    const container = document.createElement('div');
    container.className = 'train-container';
    container.dataset.trainId = trainId;

    const title = document.createElement('h2');
    title.textContent = `Train ${trainId}`;
    container.appendChild(title);

    const scheduleList = document.createElement('ul');
    scheduleList.className = 'schedule-list';
    schedule.forEach((item, index) => {
        const li = document.createElement('li');
        li.textContent = `${item.stop} (${item.type})`;
        if (index === step) li.classList.add('current-step');
        scheduleList.appendChild(li);
    });
    container.appendChild(scheduleList);

    const select = document.createElement('select');
    ['Station', 'Pass'].forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        select.appendChild(option);
    });
    container.appendChild(select);

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Enter stop name';
    container.appendChild(input);

    const addButton = document.createElement('button');
    addButton.textContent = 'Add';
    addButton.addEventListener('click', () => {
        const stop = input.value.trim();
        const type = select.value;
        if (stop) {
            const li = document.createElement('li');
            li.textContent = `${stop} (${type})`;
            scheduleList.appendChild(li);
            input.value = '';
        }
    });
    container.appendChild(addButton);

    const updateButton = document.createElement('button');
    updateButton.textContent = 'Update';
    updateButton.addEventListener('click', () => {
        const updatedSchedule = Array.from(scheduleList.querySelectorAll('li')).map(li => {
            const [stop, type] = li.textContent.match(/(.+) \((.+)\)/).slice(1);
            return { stop, type };
        });
        fetch(`/set_plan/${trainId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedSchedule),
        }).then(response => {
            if (response.ok) {
                console.log(`Schedule for Train ${trainId} updated`);
                rebuildTrainContainer(trainId); // Rebuild only this train
            } else {
                console.error('Failed to update schedule');
            }
        }).catch(error => console.error('Error:', error));
    });
    container.appendChild(updateButton);

    const resetButton = document.createElement('button');
    resetButton.textContent = 'Reset';
    resetButton.addEventListener('click', () => rebuildTrainContainer(trainId));
    container.appendChild(resetButton);

    return container;
}

// Fetch train data and update the UI
function fetchTrains(fullRebuild = false) {
    fetch('/trains')
        .then(response => response.json())
        .then(data => {
            const trainsDiv = document.getElementById('trains');
            if (fullRebuild) {
                trainsDiv.innerHTML = ''; // Clear and rebuild all
                data.trains.forEach(trainId => {
                    const schedule = data.time_tables[trainId] || [];
                    const step = data.step[trainId] !== undefined ? data.step[trainId] : -1;
                    const container = buildTrainContainer(trainId, schedule, step);
                    trainsDiv.appendChild(container);
                });
            } else {
                // Update steps and manage train additions/removals
                const existingContainers = Array.from(trainsDiv.querySelectorAll('.train-container'));
                const newTrainIds = data.trains;

                // Remove trains no longer present
                existingContainers.forEach(container => {
                    if (!newTrainIds.includes(container.dataset.trainId)) {
                        container.remove();
                    }
                });

                // Add or update trains
                newTrainIds.forEach(trainId => {
                    const schedule = data.time_tables[trainId] || [];
                    const step = data.step[trainId] !== undefined ? data.step[trainId] : -1;
                    let container = existingContainers.find(c => c.dataset.trainId === trainId);
                    if (!container) {
                        // New train
                        container = buildTrainContainer(trainId, schedule, step);
                        trainsDiv.appendChild(container);
                    } else {
                        // Update step highlight only
                        const scheduleList = container.querySelector('.schedule-list');
                        const items = scheduleList.querySelectorAll('li');
                        items.forEach(item => item.classList.remove('current-step'));
                        if (step >= 0 && step < items.length) {
                            items[step].classList.add('current-step');
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Error fetching trains:', error));
}

// Rebuild a single train’s container
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

// Initial load
fetchTrains(true);

// Periodic step updates (every 5 seconds)
setInterval(() => fetchTrains(false), 5000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    app.run(port=9998, host="0.0.0.0")
