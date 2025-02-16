
# this will map a track that meets the reuirements specified on github https://github.com/b31556/intelino

from intelino.trainlib import TrainScanner
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision
)
import random
import time
import json

map={}

timetable={}

valtok=[]

currentzone_beggining=None

form_time=None

autoincrecemt=0

def checkdone():
    global map
    global valtok
    for v in valtok:
        for i in (0,1,"-"):
            if not (v[0],v[1],i) in map:
                return False
    return True

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

def detect(train, msg):
    global trainc
    if msg.color==C.BLACK:
        if train in trainc.keys():
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

def command(train, colors):
    global map,valtok,currentzone_beggining,form_time,autoincrecemt,timetable
    
    if colors[2] == 'C':
        if currentzone_beggining:
            map[currentzone_beggining]=autoincrecemt
            if not( (colors[1],colors[0],0) in map or (colors[1],colors[0],1) in map ):
                map[(colors[1],colors[0],"?")] =autoincrecemt
            timetable[autoincrecemt] = time.time()-form_time
            autoincrecemt+=1
            if not (colors[1],colors[0]) in valtok:
                valtok.append((colors[1],colors[0]))
            if checkdone():
                print("Done!")
                with open("map.json","w") as f:
                    json.dump(map,f)
                with open("timetable.json","w") as f:
                    json.dump(timetable,f)
                time.sleep(1)
                train.stop_driving()
                exit()

        
        currentzone_beggining=(colors[1],colors[0],"-")
        form_time=time.time()
        
    if colors[0] == 'C':
        if currentzone_beggining:
            map[currentzone_beggining]=autoincrecemt
            map[(colors[1],colors[2],"-")] =autoincrecemt
            timetable[autoincrecemt] = time.time()-form_time
            autoincrecemt+=1
            if not (colors[1],colors[2]) in valtok:
                valtok.append((colors[1],colors[2]))
            if checkdone():
                print("Done!")
                with open("map.json","w") as f:
                    json.dump(map,f)
                with open("timetable.json","w") as f:
                    json.dump(timetable,f)
                time.sleep(1)
                train.stop_driving()
                exit()
        
        ch=[]

        if not (colors[1],colors[2],0) in map:
            ch.append(0)
        elif not (colors[1],colors[2],1) in map:
            ch.append(1)
        else:
            ch.append(random.choice((0,1)))

        currentzone_beggining=(colors[1],colors[2],ch)
        form_time=time.time()

        train.set_next_split_steering_decision(SteeringDecision.LEFT if ch==0 else SteeringDecision.RIGHT)
        
    

def main():
    with TrainScanner() as train:
        train.add_front_color_change_listener(detect)
        train.set_snap_command_execution(False)
        train.drive_at_speed(60)
        

        


if __name__ == "__main__":
    main()
