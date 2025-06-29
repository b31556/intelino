# CSÁT TEST TRAIN SIMULATOR WITHOUT INTELINO
# lets us click buttons instead of using actual hardware

import json
import time
from flask import Flask, request, jsonify

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

@app.route("/test/set_plan/<train_id>", methods=['POST'])
def test_set_plan(train_id):
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

if __name__ == '__main__':
    app.run(port=5081)