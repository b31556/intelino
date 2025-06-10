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
    return flask.render_template("index.html")

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    app.run(port=9998, host="0.0.0.0")
