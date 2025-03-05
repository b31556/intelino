
# please visit the github page if you dont know how to use it  https://github.com/b31556/intelino


import random
import time
from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision
)
from intelino.trainlib.messages import TrainMsgEventSnapCommandDetected

train_waiting=[]

trains={}

trainc={}

zones={}

MAP={}

danger_zones={}
danger_zones_trains_waiting={}

trains_last={}

data = {
    ("R","M",0): 0,
    ("R","M",1): 1,
    ("B","G",0): 1,
    ("B","G",1): 0,
    ("B","W","-"): 2,
    ("R","M","-"): 2,
    ("B","G","-"): 3,
    ("B","W",0): 3,
    ("B","W",1): 4,
    ("B","Y","-"): 4,
    ("B","Y",0): 5,
    ("B","Y",1): 5,
}

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

def find_next(colors):
    intakes=[]
    for ctrl in data:
        if data[ctrl] == data[colors]:
            intakes.append(ctrl)
    intakes.remove(colors)
    next_valto = intakes[0]
    return next_valto


def check_ultimake_danger(colors):
    global MAP
    next_valto = find_next(colors)
    if next_valto[2] == "-":
        if not((next_valto[0],next_valto[1],0) in MAP) and not((next_valto[0],next_valto[1],1) in MAP):
            return True
        else:
            return False
    else:
        if not(data[(next_valto[0],next_valto[1],'-')] in MAP):
            return check_ultimake_danger((next_valto[0],next_valto[1],'-'))
        else:
            return False


def mark_path(train, colors, isstart=False):
    global MAP
    
    if not isstart:
        MAP[data[colors]]=train
    
    intakes=[]
    for ctrl in data:
        if data[ctrl] == data[colors]:
            intakes.append(ctrl)
    intakes.remove(colors)
    next_valto = intakes[0]
    if next_valto[2] == "-":
        if not((next_valto[0],next_valto[1],0) in MAP) and not((next_valto[0],next_valto[1],1) in MAP):
            return True
        else:
            return False
    else:
        if not(data[(next_valto[0],next_valto[1],'-')] in MAP):
            return mark_path(train,(next_valto[0],next_valto[1],'-'))
        else:
            return False



def makedecision(train,colors):
    global MAP
    global data
    "returns 0 for left and 1 for right"
    posibilities=[]
    if not data[(colors[1],colors[2],0)] in MAP:
        if check_ultimake_danger((colors[1],colors[2],0)):
            posibilities.append(0)

        
                


    if not data[(colors[1],colors[2],1)] in MAP:
        if check_ultimake_danger((colors[1],colors[2],1)):
            posibilities.append(1)
        

    if len(posibilities) == 0:
        train.stop_driving()
        print("ERROR PROBLAMEA")




    print(f"posible to go {posibilities}")
    
    try:
        dec=random.choice(posibilities)
    except:
        return 0
    mark_path(train,(colors[1],colors[2],dec))

    print(dec)



    return dec







def detect(train, msg):
    global trainc, MAP, trains_last
    if msg.color==C.BLACK:
        if train in trainc.keys():
            if trainc[train]==["M"]:
                command(train,find_next(trains_last[train]))
            del trainc[train]
        return
    else:
        if train in trainc.keys():
            trainc[train].append(col(msg.color))
        else:
            trainc[train]=[col(msg.color)]
            return
    
    if len(trainc[train]) >=3:
        command(train, trainc[train])

def command(train: Train, colors: list):
    global trains
    global train_waiting
    global zones
    global danger_zones
    global danger_zones_trains_waiting
    global trains_last
    print(colors)

    if colors[0] == 'W' and colors[2] == 'W':
        if colors[1] in danger_zones:
            if danger_zones[colors[1]] == train:
                del danger_zones[colors[1]]
                try:
                    tostarttrain=danger_zones_trains_waiting[colors[1]].pop(0)
                    tostarttrain.drive_at_speed(50)
                    danger_zones[colors[1]] = tostarttrain
                except:
                    pass
            else:
                train.stop_driving()
                if colors[1] in danger_zones_trains_waiting:
                    danger_zones_trains_waiting[colors[1]].append(train)
                else:
                    danger_zones_trains_waiting[colors[1]] = [train]
        else:
            danger_zones[colors[1]] = train


    if colors[2] == 'C':
        todel=False
        for mop in MAP:
            if MAP[mop] == train:
                todel=mop
        if not todel == False:
            del MAP[todel]
        
        if data[(colors[1],colors[0],"-")] in MAP:
            train.stop_driving()
        print("train in zone ", data[(colors[1],colors[0],"-")])
        MAP[data[(colors[1],colors[0],"-")]] = train
        trains_last[train] = (colors[1],colors[0],"-")


    if colors[0] == 'C':
        todel=[]
        for mop in MAP:
            if MAP[mop] == train:
                todel.append(mop)
        for ot in todel:
            del MAP[ot]
        
        ch= makedecision(train,colors)
        print("train in zone ", data[(colors[1],colors[2],ch)])
        

        
        
        

        MAP[data[(colors[1],colors[2],ch)]] = train
        
        train.set_next_split_steering_decision(SteeringDecision.LEFT if ch == 0 else SteeringDecision.RIGHT)
        print("left" if ch == 0 else "right")

        trains_last[train] = (colors[1],colors[2],ch)

    

def main():
    global trains
    global train_in_danger_zone

    train_count = 2
    blink_delay = 0.5  # in seconds

    print("scanning and connecting...")

    trains_list = TrainScanner(timeout=4.0).get_trains(train_count)

    print("connected train count:", len(trains))

    for t in trains_list:
        #t.drive_at_speed(random.randint(30,60))
        t.add_front_color_change_listener(detect)
        t.set_snap_command_execution(False)
        trains[t.id]=t
        
    

    print("disconnecting...")
    i=input("press enter to exit >")

    # cleanup
    for train in trains_list:
        train.set_top_led_color(0, 0, 0)
        train.set_headlight_color()
        train.stop_driving()
        train.disconnect()


if __name__ == "__main__":
    main()
