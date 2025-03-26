from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection)
import random

def col(color):
    if color == C.GREEN:
        return "G"
    elif color == C.RED:
        return "R"
    elif color == C.BLUE:
        return "B"
    elif color == C.YELLOW:
        return "Y"
    elif color == C.MAGENTA:
        return "M"
    elif color == C.WHITE:
        return "W"
    elif color == C.CYAN:
        return "C"
    
def detect(train, msg, trainc):
    if msg.color==C.MAGENTA:
        if not(train in trainc.keys()):
            global irany
            irany=random.randint(0,1)

            print(irany)
            train.set_next_split_steering_decision(SteeringDecision.LEFT if irany==0 else SteeringDecision.RIGHT)


    if msg.color==C.BLACK:
        if train in trainc.keys():
            del trainc[train]
        return {"tc":trainc}
    else:
        if train in trainc.keys():
            trainc[train].append(col(msg.color))
        else:
            trainc[train]=[col(msg.color)]
            return {"tc":trainc}
    
    if len(trainc[train]) >=3:
        return {"cmd":(train, trainc[train]),"tc": trainc}

    return {"tc":trainc}