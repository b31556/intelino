import json
import random
import time
from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision
)
from intelino.trainlib.messages import TrainMsgEventSnapCommandDetected



trains_list = TrainScanner(timeout=4.0).get_trains(1)

MAP=[(1,1):(2,1), (1,1):(1,2), (1,1):(1,2)]

class MT:
    def __init__(self, train):
        self.train = train

def route(fr,to):
    for 

def detect(train:Train,msg:TrainMsgEventSnapCommandDetected):
    colors=msg.colors
    if colors.start_with(C.CYAN):
