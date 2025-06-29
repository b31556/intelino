# CSÁT TEST TRAIN SIMULATOR WITHOUT INTELINO
# lets us click buttons instead of using actual hardware

import json
import time
from flask import Flask, request, jsonify
import flask
from flask_cors import CORS
import os


import navigate  # your pathfinding logic

from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection
)

app = Flask(__name__)

with open("intelino/real/map.json", "r") as f:
    MAP = json.load(f)

SPEED = 50
CORS(app, origins=["*"], supports_credentials=True) 
# Virtual train world state
TRAINS = ["virtual_train"]
LAST_STATION = {"virtual_train": "fo-1"}
DESTINATION = {"virtual_train": "fo-1"}
POSITION = {"virtual_train": "fo-1"}
NEXT_STATION = {"virtual_train": "fo-1"}
MOVEMENT_DIRECTION = {"virtual_train": False}
IMMUNITY = {"virtual_train": 0}
WAITING_LINE = []

def make_occupation(train):
    return [pos for k, pos in POSITION.items() if k != train] + [nxt for k, nxt in NEXT_STATION.items() if k != train]

def is_next_a_turn(train=None, plan=None):
    if plan is None:
        plan, direction, stations = navigate.route(POSITION[train], DESTINATION[train], make_occupation(train), LAST_STATION[train])
    if not plan:
        return False
    decision = plan.pop(0)
    if isinstance(decision, int):
        print(f"Virtual Train {train}: SET TURN", "LEFT" if decision == 0 else "RIGHT")
        return SteeringDecision.LEFT if decision == 0 else SteeringDecision.RIGHT

def process_queue():
    for train in WAITING_LINE[:]:
        result = set_plan(train, DESTINATION[train])
        if result:
            WAITING_LINE.remove(train)

def handle_station(train):
    if time.time() - IMMUNITY[train] < 2:
        return "IMMUNE"

    LAST_STATION[train] = POSITION[train]
    POSITION[train] = NEXT_STATION[train]

    if POSITION[train] == DESTINATION[train]:
        return "ARRIVED"

    plan, direction, stations = navigate.route(POSITION[train], DESTINATION[train], make_occupation(train), LAST_STATION[train])
    if not plan:
        if train not in WAITING_LINE:
            WAITING_LINE.append(train)
        return "WAITING"

    if direction == 1:
        MOVEMENT_DIRECTION[train] = not MOVEMENT_DIRECTION[train]
        IMMUNITY[train] = time.time()
        NEXT_STATION[train] = stations[0]
    else:
        NEXT_STATION[train] = stations[1]

    turn = is_next_a_turn(train, plan=plan)
    process_queue()
    return {"status": "continue", "turn": turn.name if turn else None}

def handle_color_change(train):
    if time.time() - IMMUNITY[train] < 2:
        return "IMMUNE"

    LAST_STATION[train] = POSITION[train]
    POSITION[train] = NEXT_STATION[train]

    plan, direction, stations = navigate.route(POSITION[train], DESTINATION[train], make_occupation(train), LAST_STATION[train])
    if not plan:
        if train not in WAITING_LINE:
            WAITING_LINE.append(train)
        return "WAITING"

    if direction == 1:
        MOVEMENT_DIRECTION[train] = not MOVEMENT_DIRECTION[train]
        IMMUNITY[train] = time.time()
        NEXT_STATION[train] = stations[1]
    else:
        NEXT_STATION[train] = stations[1]

    turn = is_next_a_turn(train, plan=plan)
    process_queue()
    return {"status": "continue", "turn": turn.name if turn else None}

def set_plan(train_id, destination):
    train = TRAINS[int(train_id)] if isinstance(train_id, str) and train_id.isdigit() else train_id
    destination = destination.replace('"', '')
    if train in WAITING_LINE:
        WAITING_LINE.remove(train)

    DESTINATION[train] = destination
    plan, direction, stations = navigate.route(POSITION[train], destination, make_occupation(train), LAST_STATION[train])

    if not stations:
        if train not in WAITING_LINE:
            WAITING_LINE.append(train)
        return

    NEXT_STATION[train] = stations[1]
    turn = is_next_a_turn(train, plan)
    MOVEMENT_DIRECTION[train] = MOVEMENT_DIRECTION[train] if direction == 0 else not MOVEMENT_DIRECTION[train]
    IMMUNITY[train] = time.time()
    return {"turn": turn.name if turn else None}

@app.route("/graph", methods=['GET'])
def graph():
    if os.path.exists("intelino/real/map.json"):
        with open("intelino/real/map.json", "r") as f:
            map_data = json.load(f)
    else:
        with open("real/map.json", "r") as f:
            map_data = json.load(f)
    return flask.jsonify(map_data)


@app.route('/get_trains', methods=['GET'])
def get_trains():
    global TRAINS
    train_ids = [str(i) for i in range(len(TRAINS))]
    return flask.jsonify({"trains": train_ids})

@app.route("/json", methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def json_data():
    if request.method == "OPTIONS":
        return '', 200
    global POSITION, LAST_STATTION, DESTINATION, NEXT_STATION, MOVEMENT_DIRECTION
    data = {
        "trains": [
        {
                "position": POSITION[train],
                "last_station": LAST_STATION[train],
                "destination": DESTINATION[train],
                "next_station": NEXT_STATION[train],
                "movement_direction": MOVEMENT_DIRECTION[train]} for train in TRAINS
        ]
    }
    return flask.make_response(json.dumps(data), 200, {'Content-Type': 'application/json'})

@app.route("/test/set_plan/<train_id>", methods=['POST'])
def test_set_plan(train_id):
    data = request.get_data(as_text=True)
    result = set_plan(train_id, data)
    return jsonify({"message": "Plan set", "result": result})

@app.route("/set_plan/<train_id>", methods=['POST'])
def test_set_plann(train_id):
    data = request.get_data(as_text=True)
    result = set_plan(train_id, data)
    return jsonify({"message": "Plan set", "result": result})

@app.route("/test/handle_station", methods=['POST'])
def test_handle_station():
    result = handle_station("virtual_train")
    return jsonify({"message": "Handled station", "result": result})

@app.route("/test/handle_color", methods=['POST'])
def test_handle_color():
    result = handle_color_change("virtual_train")
    return jsonify({"message": "Handled color", "result": result})

@app.route("/test/set_pos", methods=['POST'])
def test_set_pos():
    data = request.get_json()
    train_id = data.get("train_id", "virtual_train")
    position = data.get("position", "fo-1")
    destination = data.get("destination", "fo-1")

    train_id=TRAINS[int(train_id)]
    
    POSITION[train_id] = position
    DESTINATION[train_id] = destination
    NEXT_STATION[train_id] = position
    return jsonify({
        "message": "Position set",
        "train_id": train_id,
        "position": POSITION[train_id],
        "destination": DESTINATION[train_id],
        "next_station": NEXT_STATION[train_id]
    })

@app.route('/get_plan/<train_id>', methods=['GET'])
def get_plan(train_id):
    global TRAINS, DESTINATION, POSITION, LAST_STATION, NEXT_STATION
    train = TRAINS[int(train_id)]
    plan, direction, stations = navigate.route(POSITION[train], DESTINATION[train], make_occupation(train), LAST_STATION[train])
    if not plan:
        plan= []
        direction = "KYS"
        stations = []
    return flask.jsonify({
        "train_id": train_id,
        "destination": DESTINATION[train],
        "position": POSITION[train],
        "last_station": LAST_STATION[train],
        "next_station": NEXT_STATION[train],
        "plan": stations,
        "direction": direction,
        "movement_direction": MOVEMENT_DIRECTION[train],
        "commands": [str(cmd) for cmd in plan]
    })

@app.route("/test/state", methods=['GET'])
def get_state():
    return jsonify({
        "position": POSITION,
        "destination": DESTINATION,
        "next_station": NEXT_STATION,
        "last_station": LAST_STATION,
        "direction": MOVEMENT_DIRECTION,
        "waiting": WAITING_LINE
    })

@app.route('/get_positions', methods=['GET'])
def get_positions():
    poses={}
    for i,key in zip(range(len(POSITION.keys())), POSITION):
        poses[str(i)]=POSITION[key]
    return flask.jsonify(poses)

if __name__ == '__main__':
    app.run(port=5080)