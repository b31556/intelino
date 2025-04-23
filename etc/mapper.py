
# this will map a track that meets the reuirements specified on github https://github.com/b31556/intelino

from intelino.trainlib import TrainScanner
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection
)
import random
import time
import json

reqdirch=False
reqdirchdone=True

map={}

timetable={}

valtok=[]

currentzone_beggining=None

form_time=None

trainc={}

autoincrecemt=0

irany=0

class titokmappa:
    def __init__(self):
        self.bank={} # {(to,from)}
    def i_arrived(self,fro,to):
        
        for key in self.bank:
            if (key[0],key[1])==to:
                if self.bank[key] == (fro[0],fro[1]):
                    return key[2]
        
        self.bank[fro] = to
        with open("bank.json","w") as f:
            for key in self.bank:
                f.write(str(key)+" : "+str(self.bank[key]) + "\n")

titkokmappaja=titokmappa()



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
    if msg.color==C.MAGENTA:
        if not(train in trainc.keys()):
            global irany
            irany=random.randint(0,1)

            print(irany)
            train.set_next_split_steering_decision(SteeringDecision.LEFT if irany==0 else SteeringDecision.RIGHT)


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
    global map,valtok,currentzone_beggining,form_time,autoincrecemt,timetable, irany,reqdirch,reqdirchdone

    if not reqdirchdone:
        return
    print(currentzone_beggining)
    with open("map.json","w") as f:
        toprintmap={}
        for key in map:
            if key[2] == "?":
                pass
            else:
                prepkey=""
                for i in range(len(key)):
                    prepkey += str(key[i])
                toprintmap[prepkey]=map[key]
        json.dump(toprintmap,f)
    with open("timetable.json","w") as f:
        json.dump(timetable,f)

    if colors[2] == 'C':
        if currentzone_beggining:
            
            if (colors[1],colors[0]) == (currentzone_beggining[0],currentzone_beggining[1]):
                map[(colors[1],colors[0],0)]=autoincrecemt
                map[(colors[1],colors[0],1)]=autoincrecemt
            
            # {(to1,to2) : (from1,from2,from3)}
            okt = titkokmappaja.i_arrived(currentzone_beggining,(colors[1],colors[0]))
            if okt != None:
                map[(colors[1],colors[0],okt)]=autoincrecemt
                map[currentzone_beggining]=autoincrecemt


            timetable[autoincrecemt] = time.time()-form_time
            autoincrecemt+=1
            if not (colors[1],colors[0]) in valtok:
                valtok.append((colors[1],colors[0]))
            if checkdone():
                print("Done!")
                with open("map.json","w") as f:
                    toprintmap={}
                    for key in map:
                        if key[2] == "?":
                            pass
                        else:
                            prepkey=""
                            for i in range(len(key)):
                               prepkey += str(key[i])
                            toprintmap[prepkey]=map[key]
                    json.dump(toprintmap,f)
                with open("timetable.json","w") as f:
                    json.dump(timetable,f)
                time.sleep(1)
                train.stop_driving()
                exit()

       
        form_time=time.time()
        ch=random.randint(0,1)
        irany=ch
        print(irany)
        train.set_next_split_steering_decision(SteeringDecision.LEFT if ch==0 else SteeringDecision.RIGHT)
      
        currentzone_beggining=(colors[1],colors[0],"-")

        
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
                    toprintmap={}
                    for key in map:
                        if key[2] == "?":
                            pass
                        else:
                            prepkey=""
                            for i in range(len(key)):
                               prepkey += str(key[i])
                            toprintmap[prepkey]=map[key]
                    json.dump(toprintmap,f)
                with open("timetable.json","w") as f:
                    json.dump(timetable,f)
                time.sleep(1)
                train.stop_driving()
                exit()
        
        

        if not (colors[1],colors[2],0) in map:
            ch=0
        elif not (colors[1],colors[2],1) in map:
            ch=1
        else:
            ch=random.choice((0,1))
        currentzone_beggining=(colors[1],colors[2],irany)

        form_time=time.time()

        
    

def main():
    train= TrainScanner().get_train()
    train.add_front_color_change_listener(detect)
    train.set_snap_command_execution(False)
    train.drive_at_speed(40)
    print("connected! ")
    while True:
        input("press enter to change direction")
        global reqdirch
        reqdirch=True
        

        


if __name__ == "__main__":
    main()
