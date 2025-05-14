import json
import random
import time

from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection
)

import flask
app=flask.Flask(__name__)


import navigate


LAST_STATTION={} #train: str

DESTINATION={} # train: str

POSITION={} # train: str

NEXT_STATION={} # train: str

trains=[]


def make_occupation(train):
    occupation=[]
    for key in POSITION:
        if key != train:
            occupation.append(POSITION[key])
    for key in NEXT_STATION:
        if key != train:
            occupation.append(NEXT_STATION[key])
    return occupation

def is_next_a_turn(train=None,plan=None):
    if plan is None:
        plan,direction,ss=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])
    
    if len(plan) == 0:
        return False
    decision=plan.pop(0)
    if isinstance(decision,int):
        train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
    
def handle_split(train,msg):
    pass

def handle_station(train,msg):
    if msg.colors[:3]==(C.WHITE,C.MAGENTA,C.WHITE) or msg.colors[:3]==(C.WHITE,C.BLACK,C.BLACK):
        global POSITION,DESTINATION,NEXT_STATION,LAST_STATTION
        LAST_STATTION[train]=POSITION[train]
        POSITION[train]=NEXT_STATION[train]

        if POSITION[train]==DESTINATION[train]:
            train.stop_driving()
            return

        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])
        
        if direction == 1:
            train.drive_at_speed(40,MovementDirection.INVERT)
            NEXT_STATION[train]=stations[0]
        else:
            NEXT_STATION[train]=stations[1]

        if len(plan) == 0:
            return False
        
        if POSITION[train] == DESTINATION[train]:
            train.stop_driving()
        
        
        is_next_a_turn(train,plan=plan)

def handle_color_change(train,msg):
    if msg.color == C.CYAN:
        global POSITION,DESTINATION,NEXT_STATION,LAST_STATTION
        LAST_STATTION[train]=POSITION[train]
        POSITION[train]=NEXT_STATION[train]
        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])
        if direction == 1:
            train.drive_at_speed(40,MovementDirection.INVERT)
            NEXT_STATION[train]=stations[0]
        else:
            NEXT_STATION[train]=stations[1]
        is_next_a_turn(train,plan=plan)
         


def main():
    global trains, POSITION, LAST_STATTION

    train_count = 1
    blink_delay = 0.5  # in seconds

    print("scanning and connecting...")

    trains_list = TrainScanner(timeout=6.0).get_trains(train_count)

    print("connected train count:", len(trains_list))

    posible_positions=["allkulon"]

    for t in trains_list:
        #t.drive_at_speed(random.randint(30,60))
        t.add_split_decision_listener(handle_split)
        t.add_front_color_change_listener(handle_color_change)
        t.add_snap_command_detection_listener(handle_station)
        t.set_snap_command_execution(False)
        t.set_snap_command_feedback(False,False)
        
        trains.append(t)

        POSITION[t] = posible_positions.pop(0)
        LAST_STATTION[t] = POSITION[t]
        print(f"train {t.id} position: {POSITION[t]}")

        


def set_plan(train_id:int,destination:str):
    destination=destination.replace('"','')
    global trains,DESTINATION,NEXT_STATION
    train=trains[int(train_id)]
    DESTINATION[train] = destination
    print(f"set plan for {train_id} from {POSITION[trains[train_id]]} to {destination}")
    plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],make_occupation(train),LAST_STATTION[train])  ##### IMPLAMENT OCCUPATION
    NEXT_STATION[train] = stations[1]
    is_next_a_turn(train,plan)
    if direction != "KYS":
        train.drive_at_speed(40,MovementDirection.FORWARD if direction==0 else MovementDirection.BACKWARD)

@app.route('/set_plan/<train_id>', methods=['POST'])
def receive_data(train_id):
    data = flask.request.get_data(as_text=True)
    print(f"Server received: {data}")
    set_plan(int(train_id),str(data))

    return flask.jsonify({"message":"done"})

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

