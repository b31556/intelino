from intelino.trainlib import TrainScanner
from intelino.trainlib.enums import (
    SnapColorValue as C,
    SteeringDecision,
    MovementDirection)
import random
import time
import json
from utils import col, detect

trainc={}

MAP=[]

def detectt(train,msg):
    global trainc
    c=detect(train,msg,trainc)
    if "cmd" in c:
        command(c["cmd"][0],c["cmd"][1])
    trainc=c["tc"]
    
def is_are_going_t_there(valto_subject,exclude):
    """returns that are not connected to anywhere"""
    founds=[0,1]
    for i in range(len(MAP)):
        if MAP[i][0] == (valto_subject[0],valto_subject[1],0) or MAP[i][0] == (valto_subject[0],valto_subject[1],1):
            if (MAP[i][1][0],MAP[i][1][1]) != exclude:
                founds.remove(MAP[i][0][2])
        
        if MAP[i][1] == (valto_subject[0],valto_subject[1],0) or MAP[i][1] == (valto_subject[0],valto_subject[1],1):
            if (MAP[i][0][0],MAP[i][0][1]) != exclude:
                founds.remove(MAP[i][1][2])

    return founds


beggining_valto=None

journalctl={}

irany=0


def command(train,colors):
    global beggining_valto,irany,journalctl
    valto=[colors[1],colors[2]] if colors[0] == "C" else [colors[1],colors[0]]
    beerkezo_irany="-" if valto[0] == "C" else -1

    beerk = (valto[0],valto[1],beerkezo_irany)
    if beggining_valto:


        if beerkezo_irany == "-":
           if not [beggining_valto,beerk] in MAP and not [beerk,beggining_valto] in MAP:

                MAP.append([beggining_valto,beerk])

                journalctl[beggining_valto]=valto
                
                print(f"Added {beggining_valto} to {beerk} to the map")

            

        if beerkezo_irany == -1:
            ch=irany
            train.set_next_split_steering_decision(SteeringDecision.LEFT if ch==0 else SteeringDecision.RIGHT)

            journalctl[beggining_valto]=valto

            if valto == (beggining_valto[0],beggining_valto[1]):
                print("You can't go back to yourself")
                MAP.append([(beggining_valto[0],beggining_valto[1],0),(beggining_valto[0],beggining_valto[1],1)])
            
            else:
                posv=is_are_going_t_there(beggining_valto,valto)
                if len(posv) == 1:
                    beerkezo_irany=posv[0]
                    beerk=(valto[0],valto[1],beerkezo_irany)
                    if not [beggining_valto,beerk] in MAP and not [beerk,beggining_valto] in MAP:
                        MAP.append([beggining_valto,beerk])

                elif len(posv) == 0:
                    print("You can't go there")
                    print("WE ARE COOKED")

                else:
                    if (valto[0],valto[1],0) in journalctl:
                        if journalctl[[valto[0],valto[1],0]] == (beggining_valto[0],beggining_valto[1]):
                            beerkezo_irany=0
                            beerk=(valto[0],valto[1],beerkezo_irany)
                            if not [beggining_valto,beerk] in MAP and not [beerk,beggining_valto] in MAP:
                                MAP.append([beggining_valto,beerk])
                    if (valto[0],valto[1],1) in journalctl:
                        if journalctl[[valto[0],valto[1],1]] == (beggining_valto[0],beggining_valto[1]):
                            beerkezo_irany=1
                            beerk=(valto[0],valto[1],beerkezo_irany)
                            if not [beggining_valto,beerk] in MAP and not [beerk,beggining_valto] in MAP:
                                MAP.append([beggining_valto,beerk])




    beggining_valto=(valto[0],valto[1],irany if beerkezo_irany == "-" else "-")

    train.stop_driving()
    print()
    train.drive_at_speed(40)














def main():
    train= TrainScanner().get_train()
    train.add_front_color_change_listener(detectt)
    train.set_snap_command_execution(False)
    train.drive_at_speed(40)
    print("connected! ")
    while True:
        input("press enter to change direction")
        global reqdirch
        reqdirch=True

main()