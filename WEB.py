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
        
        position=requests.get("http://127.0.0.1:5080/get_positions").json()
        with data_lock:
            #position = DEBUG_POSITION.copy()
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
            "destinations": DESTINATIONS
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
    <title>Train Schedule Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone@7.25.6/babel.min.js"></script>
    <script src="https://unpkg.com/react-beautiful-dnd@13.1.1/dist/react-beautiful-dnd.min.js"></script>
</head>
<body>
    <div id="root" class="min-h-screen bg-gray-100"></div>
    <script type="text/babel">
        const { useState, useEffect } = React;
        const { DragDropContext, Droppable, Draggable } = ReactBeautifulDnd;

        function App() {
            const [trains, setTrains] = useState({});
            const [newTrainId, setNewTrainId] = useState('');
            const [newStation, setNewStation] = useState('');
            const [newWaitTime, setNewWaitTime] = useState('');
            const [schedules, setSchedules] = useState({});
            const [positions, setPositions] = useState({});

            // Fetch train data on mount and periodically
            useEffect(() => {
                const fetchTrains = async () => {
                    try {
                        const response = await fetch('http://localhost:9998/trains');
                        const data = await response.json();
                        setTrains(data);
                    } catch (error) {
                        console.error('Error fetching trains:', error);
                    }
                };
                fetchTrains();
                const interval = setInterval(fetchTrains, 5000);
                return () => clearInterval(interval);
            }, []);

            // Handle adding a new train
            const addTrain = () => {
                if (newTrainId && !schedules[newTrainId]) {
                    setSchedules({ ...schedules, [newTrainId]: [] });
                    setNewTrainId('');
                }
            };

            // Handle adding a station or wait time to a train's schedule
            const addScheduleItem = (trainId) => {
                if (newStation || newWaitTime) {
                    const item = newWaitTime ? parseInt(newWaitTime) : newStation;
                    if (item) {
                        setSchedules({
                            ...schedules,
                            [trainId]: [...(schedules[trainId] || []), item]
                        });
                        setNewStation('');
                        setNewWaitTime('');
                    }
                }
            };

            // Handle drag and drop
            const onDragEnd = (result, trainId) => {
                if (!result.destination) return;
                const items = Array.from(schedules[trainId] || []);
                const [reorderedItem] = items.splice(result.source.index, 1);
                items.splice(result.destination.index, 0, reorderedItem);
                setSchedules({ ...schedules, [trainId]: items });
            };

            // Submit schedule to backend
            const submitSchedule = async (trainId) => {
                try {
                    const response = await fetch(`http://localhost:9998/set_plan/${trainId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(schedules[trainId])
                    });
                    const data = await response.json();
                    alert(data.message);
                } catch (error) {
                    console.error('Error submitting schedule:', error);
                    alert('Failed to submit schedule');
                }
            };

            // Debug: Set train position
            const setDebugPosition = async (trainId, position) => {
                try {
                    const response = await fetch('http://localhost:9998/debug_setpos', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [trainId]: position })
                    });
                    const data = await response.json();
                    setPositions({ ...positions, [trainId]: position });
                    alert(data.message);
                } catch (error) {
                    console.error('Error setting position:', error);
                    alert('Failed to set position');
                }
            };

            return (
                <div className="container mx-auto p-4">
                    <h1 className="text-3xl font-bold mb-4">Train Schedule Manager</h1>
                    
                    {/* Add New Train */}
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold mb-2">Add New Train</h2>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={newTrainId}
                                onChange={(e) => setNewTrainId(e.target.value)}
                                placeholder="Train ID"
                                className="border p-2 rounded"
                            />
                            <button
                                onClick={addTrain}
                                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                            >
                                Add Train
                            </button>
                        </div>
                    </div>

                    {/* Train Schedules */}
                    {Object.keys(schedules).map((trainId) => (
                        <div key={trainId} className="mb-6 p-4 bg-white rounded shadow">
                            <h2 className="text-xl font-semibold mb-2">Train {trainId}</h2>
                            
                            {/* Add Station/Wait Time */}
                            <div className="flex gap-2 mb-4">
                                <input
                                    type="text"
                                    value={newStation}
                                    onChange={(e) => setNewStation(e.target.value)}
                                    placeholder="Station Name"
                                    className="border p-2 rounded"
                                />
                                <input
                                    type="number"
                                    value={newWaitTime}
                                    onChange={(e) => setNewWaitTime(e.target.value)}
                                    placeholder="Wait Time (seconds)"
                                    className="border p-2 rounded"
                                />
                                <button
                                    onClick={() => addScheduleItem(trainId)}
                                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                                >
                                    Add Item
                                </button>
                            </div>

                            {/* Drag and Drop Schedule */}
                            <DragDropContext onDragEnd={(result) => onDragEnd(result, trainId)}>
                                <Droppable droppableId={trainId}>
                                    {(provided) => (
                                        <div
                                            {...provided.droppableProps}
                                            ref={provided.innerRef}
                                            className="bg-gray-100 p-4 rounded min-h-[100px]"
                                        >
                                            {schedules[trainId].map((item, index) => (
                                                <Draggable key={`${trainId}-${index}`} draggableId={`${trainId}-${index}`} index={index}>
                                                    {(provided) => (
                                                        <div
                                                            ref={provided.innerRef}
                                                            {...provided.draggableProps}
                                                            {...provided.dragHandleProps}
                                                            className="bg-white p-2 mb-2 rounded shadow"
                                                        >
                                                            {typeof item === 'number' ? `${item} seconds` : item}
                                                        </div>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </div>
                                    )}
                                </Droppable>
                            </DragDropContext>

                            {/* Submit Schedule */}
                            <button
                                onClick={() => submitSchedule(trainId)}
                                className="mt-4 bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
                            >
                                Submit Schedule for Train {trainId}
                            </button>

                            
                        </div>
                    ))}
                </div>
            );
        }

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>"""

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    app.run(port=9998, host="0.0.0.0")
