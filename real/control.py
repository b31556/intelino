import json
import random
import threading
import time

from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection
)

import flask
app=flask.Flask(__name__)

import matplotlib.pyplot as plt
import networkx as nx
import io

import navigate

SPPEEEDDD=50

try:
    with open("intelino/real/map.json","r") as f:
        MAP=json.loads(f.read())
except FileNotFoundError:
    with open("real/map.json","r") as f:
        MAP=json.loads(f.read())

LAST_STATTION={} #train: str

DESTINATION={} # train: str

DESTINATION_GROUP={} # train: str, only while the train was sent to a station group ("fo"), DESTINATION holds the stub picked for it

RESERVE_COMMITTED_NODES=True # also keep other trains off the nodes a train is committed to. False lets them pass sooner (fewer stalls in the simulation) but relies on a train always stopping on its marker

COMMITTED_NODES={} # train: list[str], the nodes after NEXT_STATION the train can no longer avoid (see navigate.commit_end). Nobody else may take them and the train can't pick another way up to the last one

STATE_LOCK=threading.RLock() # BLE callbacks and flask threads share the dicts above, checking a node and claiming it must be one step

POSITION={} # train: str

NEXT_STATION={} # train: str

MOVEMENT_DIRECTION={}

IMMUNITY={}

TRAINS_IN_WATITING_LINE=[]

trains=[]

def process_que():
    global TRAINS_IN_WATITING_LINE
    if len(TRAINS_IN_WATITING_LINE) != 0:
        for train in list(TRAINS_IN_WATITING_LINE):  # set_plan edits the list while we loop
            try:
                set_plan(trains.index(train), DESTINATION_GROUP.get(train, DESTINATION[train]))
            except Exception as e:   # one train that can not be routed must not stop the others from retrying
                print(f"train {train.alias} still waiting: {e}")
    else:
        return



def make_occupation(train):
    occupation=[]
    for key in POSITION:
        if key != train:
            occupation.append(POSITION[key])
    for key in NEXT_STATION:
        if key != train:
            occupation.append(NEXT_STATION[key])
    if RESERVE_COMMITTED_NODES:
        for key in COMMITTED_NODES:
            if key != train:
                occupation.extend(COMMITTED_NODES[key])
    return occupation

def forced_exit_of(train):
    """The only node (besides turning back) the train can go to first: the one it is heading to when it is between two nodes, else its committed exit"""
    heading=NEXT_STATION.get(train)
    committed=COMMITTED_NODES.get(train)
    return heading if heading not in (None,POSITION[train]) else (committed[0] if committed else None)

def resolve_destination(train,strict=False):
    """For a train sent to a station group, make DESTINATION[train] a concrete free stub of it.
    Keeps the current pick while it is still free. Returns False if the group is full right now.
    A station that can not be reached at all raises when strict (a new plan), otherwise the train just waits."""
    group=DESTINATION_GROUP.get(train)
    if group is None:
        return True
    members=navigate.station_groups()[group]
    if POSITION[train] in members:   # standing on a stub of the station = arrived, any stub will do
        DESTINATION[train]=POSITION[train]
        return True
    occupation=make_occupation(train)
    reserved=[DESTINATION[other] for other in DESTINATION if other != train]
    if DESTINATION.get(train) in members and DESTINATION[train] not in occupation and DESTINATION[train] not in reserved:
        return True
    try:
        pick=navigate.pick_from_group(group,POSITION[train],LAST_STATTION[train],occupation,reserved,forced_exit_of(train))
    except Exception as e:
        if strict:
            raise
        print(f"train {train.alias} at {POSITION[train]} cannot reach station {group}: {e}")
        pick=None
    if pick is None:
        DESTINATION[train]=group   # nothing to route to yet, process_que retries
        return False
    DESTINATION[train]=pick
    return True

def wait_in_queue(train):
    if train not in TRAINS_IN_WATITING_LINE:
        TRAINS_IN_WATITING_LINE.append(train)
    train.stop_driving()
    # a train that waits only keeps what it physically sits on: the exit it already passed the split for if it stands on a switch, nothing more
    committed=COMMITTED_NODES.get(train) or []
    COMMITTED_NODES[train]=committed[:1] if navigate.is_switch(POSITION[train]) else []

def claim(train,stations):
    """The train starts towards stations[1]; from then on it also holds every node after it that leaves it no choice."""
    NEXT_STATION[train]=stations[1]
    COMMITTED_NODES[train]=navigate.committed_nodes(stations)

def advance(train):
    """Route from where the train stands now and claim its next node. Call with STATE_LOCK held.
    Returns the switch commands to steer by, or None if the train has to wait."""
    try:
        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train],forced_exit_of(train))
    except Exception as e:   # destination not reachable through the exit the train is committed to
        print(f"train {train.alias} at {POSITION[train]} cannot reach {DESTINATION[train]}: {e}")
        plan=False
    if plan==False:
        wait_in_queue(train)
        return None
    if direction == 1:
        train.drive_at_speed(SPPEEEDDD,MovementDirection.INVERT)
        MOVEMENT_DIRECTION[train] = not(MOVEMENT_DIRECTION[train])
        IMMUNITY[train] = time.time()
    claim(train,stations)
    return plan

def is_next_a_turn(train=None,plan=None):
    if plan is None:
        plan,direction,ss=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])
    
    print(plan)
    if len(plan) == 0:
        return False
    decision=plan.pop(0)
    if isinstance(decision,int):
        print(decision)
        time.sleep(0.5)
        train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
    
def handle_split(train,msg):
    pass

def handle_station(train,msg):
    global POSITION,DESTINATION,NEXT_STATION,LAST_STATTION,IMMUNITY,MOVEMENT_DIRECTION
    if time.time() - IMMUNITY[train] < 2:
        return
    if msg.colors[:3]==(C.WHITE,C.MAGENTA,C.WHITE) or msg.colors[:3]==(C.WHITE,C.BLACK,C.BLACK):
        with STATE_LOCK:
            LAST_STATTION[train]=POSITION[train]
            POSITION[train]=NEXT_STATION[train]

            plan=None
            if not resolve_destination(train):   # sent to a station group that is full right now
                wait_in_queue(train)
            elif POSITION[train]==DESTINATION[train]:
                train.stop_driving()
                COMMITTED_NODES[train]=[]
            else:
                plan=advance(train)

        if plan:
            is_next_a_turn(train,plan=plan)   # sleeps, so not under the lock

        process_que()  # we left the previous node, trains waiting on it can retry

def handle_color_change(train,msg):
    if msg.color == C.CYAN:
        
        global POSITION,DESTINATION,NEXT_STATION,LAST_STATTION,TRAINS_IN_WATITING_LINE
        with STATE_LOCK:
            LAST_STATTION[train]=POSITION[train]
            POSITION[train]=NEXT_STATION[train]

            plan=None
            if not resolve_destination(train):   # sent to a station group that is full right now
                wait_in_queue(train)
            else:
                plan=advance(train)

        if plan:
            is_next_a_turn(train,plan=plan)

        process_que()

def main():
    global trains, POSITION, LAST_STATTION, MOVEMENT_DIRECTION

    train_count = 2
    blink_delay = 0.5  # in seconds

    print("scanning and connecting...")

    trains_list = TrainScanner(timeout=6.0).get_trains(train_count)

    print("connected train count:", len(trains_list))

    posible_positions=["fo-1","fo-2"]

    for t in trains_list:
        #t.drive_at_speed(random.randint(30,60))
        t.add_split_decision_listener(handle_split)
        t.add_front_color_change_listener(handle_color_change)
        t.add_snap_command_detection_listener(handle_station)
        t.set_snap_command_execution(False)
        t.set_snap_command_feedback(False,False)
        
        #trains.append(t)

        POSITION[t] = posible_positions.pop(0)
        LAST_STATTION[t] = POSITION[t]
        MOVEMENT_DIRECTION[t] = False
        print(f"train {t.alias} position: {POSITION[t]}")

    trains=[]
    for key,_ in POSITION.items():
        trains.append(key)

        


def start_plan(train,train_id,destination):
    """Everything set_plan decides and claims. Call with STATE_LOCK held. Returns (plan, direction) or None if the train does not start."""
    global DESTINATION,NEXT_STATION,TRAINS_IN_WATITING_LINE
    if train in TRAINS_IN_WATITING_LINE:
        TRAINS_IN_WATITING_LINE.remove(train)
    DESTINATION[train] = destination
    if destination in navigate.station_groups():
        DESTINATION_GROUP[train] = destination
        try:
            resolved=resolve_destination(train,strict=True)
        except Exception:   # nothing of this station can be reached from here, tell the caller like for a single station
            DESTINATION_GROUP.pop(train,None)
            raise
        if not resolved:   # every stub of the station is taken, wait for one to free up
            if train not in TRAINS_IN_WATITING_LINE:
                TRAINS_IN_WATITING_LINE.append(train)
            return None
    else:
        DESTINATION_GROUP.pop(train,None)
    if POSITION[train] == DESTINATION[train]:   # already there
        return None
    print(f"set plan for {train_id} from {POSITION[train]} to {destination}")
    # a train between two nodes can only go on to the node it is heading to, one standing on a node only through the exit it is committed to
    plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train],forced_exit_of(train))
    if not stations:
        if train not in TRAINS_IN_WATITING_LINE:
            TRAINS_IN_WATITING_LINE.append(train)
        return None
    claim(train,stations)
    return plan,direction

def set_plan(train_id:int,destination:str):
    destination=destination.replace('"','')
    global trains
    train=trains[int(train_id)]
    with STATE_LOCK:
        started=start_plan(train,train_id,destination)
    if started is None:
        return
    plan,direction=started
    is_next_a_turn(train,plan)   # sleeps, so not under the lock
    if direction != "KYS":
        train.drive_at_speed(SPPEEEDDD,MovementDirection.FORWARD if (MOVEMENT_DIRECTION[train] if direction==0 else not(MOVEMENT_DIRECTION[train])) else MovementDirection.BACKWARD)
        MOVEMENT_DIRECTION[train]=(MOVEMENT_DIRECTION[train] if direction==0 else not(MOVEMENT_DIRECTION[train]))
        IMMUNITY[train] = time.time()

@app.route("/json")
def json_data():
    global POSITION, LAST_STATTION, DESTINATION, NEXT_STATION, MOVEMENT_DIRECTION
    data = {
        "trains": [
            {
                "id": train.id,
                "alias": train.alias,
                "position": POSITION[train],
                "last_station": LAST_STATTION[train],
                "destination": DESTINATION[train],
                "next_station": NEXT_STATION[train],
                "movement_direction": MOVEMENT_DIRECTION[train],
                "colors": train.colors,
                "speed": train.speed,
                "battery": train.battery} for train in trains
        ]
    }
    return flask.jsonify(data)


@app.route('/get_plan/<train_id>', methods=['GET'])
def get_plan(train_id):
    global trains, DESTINATION, POSITION, LAST_STATTION, NEXT_STATION
    train = trains[int(train_id)]
    plan, direction, stations = navigate.route(POSITION[train], DESTINATION[train], make_occupation(train), LAST_STATTION[train])
    if not plan:
        plan=[]
        direction="KYS"
        stations=[]
        
    return flask.jsonify({
        "train_id": train_id,
        "destination": DESTINATION[train],
        "position": POSITION[train],
        "last_station": LAST_STATTION[train],
        "next_station": NEXT_STATION[train],
        "plan": stations,
        "direction": direction,
        "movement_direction": MOVEMENT_DIRECTION[train],
        "commands": [str(cmd) for cmd in plan]
    })

@app.route('/set_plan/<train_id>', methods=['POST'])
def receive_data(train_id):
    data = flask.request.get_data(as_text=True)
    print(f"Server received: {data}")
    set_plan(int(train_id),str(data))

    return flask.jsonify({"message":"done"})

@app.route("/graph", methods=['GET'])
def graph():
    if os.path.exists("intelino/real/map.json"):
        with open("intelino/real/map.json", "r") as f:
            map_data = json.load(f)
    else:
        with open("real/map.json", "r") as f:
            map_data = json.load(f)
    return flask.jsonify(map_data)

@app.route('/groups', methods=['GET'])
def groups():
    return flask.jsonify(navigate.station_groups())

@app.route('/get_trains', methods=['GET'])
def get_trains():
    global trains
    train_ids = [train.id for train in trains]
    return flask.jsonify({"trains": train_ids})

@app.route('/get_destinations', methods=['GET'])
def get_destinations():
    poses={}
    for key in DESTINATION:
        poses[str(key.id)]=DESTINATION[key]
    return flask.jsonify(poses)

@app.route('/get_next_stations', methods=['GET'])
def get_next_stations():
    poses={}
    for key in NEXT_STATION:
        poses[str(key.id)]=NEXT_STATION[key]
    return flask.jsonify(poses)

@app.route('/get_positions', methods=['GET'])
def get_positions():
    poses={}
    for key in POSITION:
        poses[str(key.id)]=POSITION[key]
    return flask.jsonify(poses)

@app.route('/get_plans', methods=['GET'])
def get_plans():
    plans={}
    for train_id in range(len(trains)-1):
        train=trains[train_id]
        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])
        plans[train_id] = stations
    return flask.jsonify(plans)

@app.route('/web', methods=['GET'])
def web():
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Live Image Fetch</title>
  <style>
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      background: #111;
    }
    img {
      max-width: 90vw;
      max-height: 90vh;
      border: 4px solid #fff;
    }
  </style>
</head>
<body>
  <img id="liveImage" src="/img" alt="Live Image">
  <script>
    const img = document.getElementById('liveImage');
    setInterval(() => {
      img.src = `/img?cache_bust=${Date.now()}`;
    }, 1000);
  </script>
</body>
</html>
    """

@app.route('/img', methods=['GET'])
def img():
    global POSITION, LAST_STATTION, DESTINATION, NEXT_STATION
    G = nx.Graph()

    for node, neighbors in MAP.items():
        for neighbor in neighbors:
            if neighbor:
                G.add_edge(node, neighbor)

    pos = nx.spring_layout(G, seed=42)

    # Define custom coloring
    highlight_nodes = {"sw1", "st1", "stsw"}
    node_colors = ["red" if node in highlight_nodes else "skyblue" for node in G.nodes]

    highlight_edges = {(POSITION.get(train), NEXT_STATION.get(train)) for train in POSITION.keys()}
    # Normalize edges to sorted tuples (undirected graph)
    highlight_edges = {tuple(sorted(e)) for e in highlight_edges}
    edge_colors = ["red" if tuple(sorted(edge)) in highlight_edges else "gray" for edge in G.edges]

    # Plot
    plt.figure(figsize=(10, 8))
    nx.draw(
        G, pos, with_labels=True,
        node_color=node_colors,
        edge_color=edge_colors,
        node_size=1000,
        font_size=10
    )

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return flask.Response(buf.getvalue(), mimetype='image/png')


@app.route('/')
def index(): #returns a wabpage where you can see the train ids positions and destinations as well as the next stations, real time with 1 second refresh by fetching the data from the server
    return """
    <h1>Train Control Server</h1>
    <h2>Train IDs</h2>
    <a id="train_ids">
    </a>
    <h2>Train Positions</h2>
    <a id="train_positions">
    </a>
    <h2>Train Destinations</h2>
    <a id="train_destinations">
    </a>
    <h2>Next Stations</h2>
    <a id="train_next_stations">
    </a>
    <h1>Set Plan</h1>
    <form id="set_plan_form">
        <label for="train_id">Train ID:</label>
        <input type="text" id="train_id" name="train_id"><br><br>
        <label for="destination">Destination:</label>
        <input type="text" id="destination" name="destination"><br><br>
        <input type="submit" value="Set Plan">
    </form>
    <script>
        document.getElementById('set_plan_form').addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the form from submitting normally

            const trainId = document.getElementById('train_id').value;
            const destination = document.getElementById('destination').value;

            fetch('/set_plan/' + trainId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(destination)
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                alert(data);
            });
        });
        // Fetch data every second
        setInterval(function(){
            fetch('/get_trains')
            .then(response => response.json())
            .then(data => {
                document.getElementById('train_ids').innerHTML = JSON.stringify(data);
            });
            fetch('/get_positions')
            .then(response => response.json())
            .then(data => {
                document.getElementById('train_positions').innerHTML = JSON.stringify(data);
            });
            fetch('/get_destinations')
            .then(response => response.json())
            .then(data => {
                document.getElementById('train_destinations').innerHTML = JSON.stringify(data);
            });
            fetch('/get_next_stations')
            .then(response => response.json())
            .then(data => {
                document.getElementById('train_next_stations').innerHTML = JSON.stringify(data);
            });
        }, 500);
    </script>
    """





if __name__=='__main__':
    main()
    app.run(port=5080,debug=False,use_reloader=False)

