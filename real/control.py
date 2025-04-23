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

PLAN={} #train: [plan]

trains=[]

def handle_split(train,msg):
    global PLAN

    plan=list(PLAN[train])

    if len(plan) != 0:
        if isinstance(PLAN[train][0],int):
            decision=PLAN[train].pop(0)
            train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
        print("set decision")

def handle_station(train,msg):
    if msg.colors==(C.WHITE,C.MAGENTA,C.GREEN,C.BLACK):
        pp = PLAN[train].pop(0)

        if pp == "pass":
            pass
        elif pp=="stop":
            train.stop_driving()
        else:
            raise SyntaxError
        
        if len(PLAN[train]) != 0:
            if isinstance(PLAN[train][0],int):
                decision=PLAN[train].pop(0)
                train.set_next_split_steering_decision(SteeringDecision.LEFT if decision==0 else SteeringDecision.RIGHT)
    

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
        t.add_snap_command_detection_listener(handle_station)
        t.set_snap_command_execution(False)
        t.set_snap_command_feedback(False,False)
        
        trains.append(t)
        
    


def set_plan(train_id,plan):
    global trains,PLAN
    PLAN[trains[train_id]] = plan
    if isinstance(PLAN[trains[train_id]][0],int):
        decision=PLAN[trains[train_id]].pop(0)
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
    start_train(train_id,)

    return flask.jsonify({"message":"done"})

main()

