import flask
import public_navigation.final as pn  # your module that does the real stuff
import requests
import threading
import json
import time
import os

app = flask.Flask(__name__)

TIME_TABLES = {}    # train_id: list[str]
DESTINATIONS = {}   # train_id: str
AT = {}           # train_id: int
POSITION = {0:"st1"}  # train_id: str
TRAINS= [] # list of train IDs eg 0 1 2 etc
COONNECTED = False  # flag to check if the server is connected to the intelino server

data_lock = threading.Lock()



def do_after_arrival(train_id, waittime):
    time.sleep(waittime)
    with data_lock:
        if waittime != 0:
            AT[str(train_id)] += 1
            if int(AT[str(train_id)]) >= len(TIME_TABLES[str(train_id)]):
                AT[str(train_id)] = 0
        
        print(f"[AFTER] {waittime}s passed since {train_id} arrived we go to ")
        while isinstance(TIME_TABLES[str(train_id)][AT[str(train_id)]], int):
            print(f"Waiting for {TIME_TABLES[str(train_id)][AT[str(train_id)] - 1]} seconds")
            time.sleep(TIME_TABLES[str(train_id)][AT[str(train_id)] - 1])
            AT[str(train_id)] += 1
            if int(AT[str(train_id)]) >= len(TIME_TABLES[str(train_id)]):
                AT[str(train_id)] = 0
        
        DESTINATIONS[str(train_id)] = TIME_TABLES[str(train_id)][AT[str(train_id)]]
        requests.post(f"http://127.0.0.1:5080/set_plan/{train_id}", data=TIME_TABLES[str(train_id)][AT[str(train_id)]])  # or maybe do something else



def main_loop():
    
    while True:
        global COONNECTED,TRAINS,POSITION,DESTINATIONS,AT
        try:
            position=requests.get("http://127.0.0.1:5080/get_positions").json()
        except:
            time.sleep(5)
            print("Waiting for intelino server to start...")
            with data_lock:
                COONNECTED = False
            continue
        with data_lock:
            
            COONNECTED = True
            TRAINS=list(range(len(position.keys())))
            c=0
            pok=list(position.values())
            pok.reverse()
            for pp in pok:
                POSITION[c] = pp
                c+=1
            for train_id in TRAINS:
                try:
                    if pok[int(train_id)] == DESTINATIONS[str(train_id)]:
                        print(f"{train_id} arrived at {list(position.values())[int(train_id)]}")
            
                        if AT[str(train_id)] == -1:
                            continue  # skip if the train is not following a timetable
                        AT[str(train_id)] += 1
                        if AT[str(train_id)] >= len(TIME_TABLES[str(train_id)]):
                            AT[str(train_id)] = 0
                        if isinstance(TIME_TABLES[str(train_id)][AT[str(train_id)]], int):
                            waittime= TIME_TABLES[str(train_id)][AT[str(train_id)]]
                        else:
                            waittime= 0
                            #print(f"Waiting for {waittime} seconds")
                        
                        DESTINATIONS[str(train_id)] =False
                
                        t = threading.Thread(target=do_after_arrival, args=(train_id, waittime), daemon=True)
                        t.start()

                        
                except:
                    pass
                
        time.sleep(1)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response 

@app.route("/save/<save_name>/<train_id>")
def save(save_name, train_id):
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED
    if not os.path.exists("saves"):
        os.makedirs("saves")
    try:
        with open(f"saves/{save_name}.json", "w") as f:
            json.dump(TIME_TABLES[train_id], f)
        print(f"Data saved to saves/{save_name}.json")
    except Exception as e:
        print(f"Error saving data: {e}")
        return flask.jsonify({"error": str(e)}), 500
    return flask.jsonify({"message": "Data saved successfully"})
        
@app.route("/load/<save_name>/<train_id>")
def load(save_name, train_id):
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED
    if not os.path.exists(f"saves/{save_name}.json"):
        return flask.jsonify({"error": "Save file not found"}), 404
    try:
        with open(f"saves/{save_name}.json", "r") as f:    
            TIME_TABLES[train_id] = json.load(f)
            DESTINATIONS[train_id] = TIME_TABLES[train_id][0]
            AT[train_id] = 0

            if COONNECTED:
                AT[train_id] += 1
                if isinstance(TIME_TABLES[train_id][0], int):
                    do_after_arrival(train_id, TIME_TABLES[train_id][0])
                else:
                    try:
                        requests.post(f"http://127.0.0.1:5080/set_plan/{train_id}", data=TIME_TABLES[train_id][AT[train_id]])
                    except requests.exceptions.RequestException as e:
                        AT[train_id] -= 1
            
        print(f"Data loaded from saves/{save_name}.json")
    except Exception as e:
        print(f"Error loading data: {e}")
        return flask.jsonify({"error": str(e)}), 500
    return flask.jsonify({"message": "Data loaded successfully"})


@app.route("/send/<train_id>", methods=["POST"])
def send(train_id):
    data= flask.request.get_data(as_text=True).replace("\"", '')
    if not data:
        return flask.jsonify({"message": "No data provided"}), 400
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED
    
    DESTINATIONS[train_id] = data
    try:
        requests.post(f"http://127.0.0.1:5080/set_plan/{train_id}", data=data)
    except requests.exceptions.RequestException as e:
        pass

    print(f"Data sent to train {train_id}: {data}")
    return flask.jsonify({"message": "Data sent successfully"})

@app.route("/toggle/<train_id>/<onoff>", methods=["GET"])
def toggle(train_id, onoff):
    if onoff.lower() not in ["on", "off"]:
        return flask.jsonify({"message": "Invalid toggle value"}), 400
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED
    
    if onoff.lower() == "on":
        AT[train_id] = 0
        DESTINATIONS[train_id] = TIME_TABLES[train_id][0]
        print(f"Train {train_id} toggled ON")
        requests.post(f"http://127.0.0.1:5080/set_plan/{train_id}", data=TIME_TABLES[train_id][AT[train_id]])  # or maybe do something else

    else:
        AT[train_id] = -1
        #DESTINATIONS[train_id] = False
        print(f"Train {train_id} toggled OFF")
    return flask.jsonify({"message": f"Train {train_id} toggled {onoff.upper()}"})

@app.route("/trains", methods=["GET"])
def get_trains():
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED,POSITION
    return flask.jsonify({
        "time_tables": TIME_TABLES,
        "step": AT,
        "trains": TRAINS,
        "connected": COONNECTED,
        "destinations": DESTINATIONS,
        "positions": POSITION
    })


@app.route("/set_plan/<train_id>", methods=["POST"])
def set_plan(train_id):
    data = flask.request.get_data(as_text=True)
    if len(json.loads(data)) == 0:
        return flask.jsonify({"message": "No plan provided"}), 400
    print(f"Server received: {data}")
    global TIME_TABLES,AT,DESTINATIONS,COONNECTED

    
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
