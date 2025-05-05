import json
import random
import time
from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection
)
from intelino.trainlib.messages import TrainMsgEventSnapCommandDetected

import flask
app=flask.Flask(__name__)


import navigate


DESTINATION={} # train: str

POSITION={} # train: str

NEXT_STATION={} # train: str

trains=[]

def replan(train):
    plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train],POSITION.items())
    train.drive_at_speed(40,MovementDirection.FORWARD if direction==0 else MovementDirection.BACKWARD)
    global NEXT_STATION
    NEXT_STATION[train]=stations[1]
    if len(plan) == 0:
        return False
    return plan.pop(0)

def is_next_turn(train=None,plan=None):
    if plan is None:
        plan=navigate.route(POSITION[train],DESTINATION[train],POSITION.items())[0]
    if len(plan) == 0:
        return False
    decision=plan(train).pop(0)
    if isinstance(decision,int):
        train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
    

def handle_split(train,msg):
    pass

def handle_station(train,msg):
    if msg.colors[:3]==(C.WHITE,C.MAGENTA,C.GREEN):
        global POSITION,DESTINATION,NEXT_STATION
        POSITION[train]=NEXT_STATION[train]

        pp = replan(train)
        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train])
        
        NEXT_STATION[train]=stations[1]
        if pp == "pass":
            is_next_turn(plan=pp)
        elif pp=="stop":
            train.stop_driving()
        elif not pp:
            train.stop_driving()
            raise Exception("no path")
        else:
            raise Exception("not understood command")

def handle_color_change(train,msg):
    if msg.color == C.CYAN:
        global POSITION,DESTINATION,NEXT_STATION
        POSITION[train]=NEXT_STATION[train]
        plan,direction,stations=navigate.route(POSITION[train],DESTINATION[train])
        NEXT_STATION[train]=stations[1]
        if is_next_turn(train):
            decision=replan(train)
            train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
            print("set decision")
         


def main():
    global trains

    train_count = 1
    blink_delay = 0.5  # in seconds

    print("scanning and connecting...")

    trains_list = TrainScanner(timeout=4.0).get_trains(train_count)

    print("connected train count:", len(trains))

    for t in trains_list:
        #t.drive_at_speed(random.randint(30,60))
        t.add_split_decision_listener(handle_split)
        t.add_front_color_change_listener(handle_color_change)
        t.add_snap_command_detection_listener(handle_station)
        t.set_snap_command_execution(False)
        t.set_snap_command_feedback(False,False)
        
        trains.append(t)
        
    


def set_plan(train_id,plan):
    global trains,PLAN
    PLAN[trains[train_id]] = plan
    if isinstance(PLAN[trains[train_id]][0],int):
        decision=replan(trains[train_id])
        trains[train_id].set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
 

def start_train(train_id,direction):
    global trains
    train=trains[train_id]
    train.drive_at_speed(40,MovementDirection.FORWARD if direction==0 else MovementDirection.BACKWARD)

@app.route('/set_plan/<train_id>', methods=['POST'])
def receive_data(train_id):
    data = flask.request.get_json()
    print(f"Server received: {data}")
    set_plan(train_id,data)

    return flask.jsonify({"message":"done"})

@app.route('/start_train/<train_id>/<direction>', methods=['POST','GET'])
def receive_data(train_id,di):
    start_train(train_id,di)

    return flask.jsonify({"message":"done"})

main()
print("started server and connected")
app.run(port=5080,debug=True)
