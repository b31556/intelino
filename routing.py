import json
import time


with open("timetable.json") as f:
    timetable = json.load(f)

data={}
with open("map.json","r") as f:
    idi = json.load(f)
    for zone in idi:
        data[(zone[0],zone[1],zone[2])] = idi[zone]


class Track:
    def __init__(self,number,time):
        self.id=number
        self.time=time
        self.appointments=[]
        self.train=None
        self.ends={}

    def is_free_at(self,fortrain,fromm):
        to=fromm+self.time
        for appointment in self.appointments:
            if not( (appointment['from'] < fromm and appointment['to'] < fromm) or (appointment['from'] > to and appointment['to'] > to)):
                if appointment['train'] != fortrain:
                    return False
        return True

    def is_free_for(self,train):
        if self.train == None:
            return True
        if self.train == train:
            return True
        return False

    def get_end(self,notend):
        for end in self.ends:
            if end != notend:
                return end,self.ends[end]


    def __str__(self):
        return self.id

class Switch:
    def __init__(self,colors,atrack,atrackrole):
        self.id=colors
        self.tracks={atrackrole:atrack}

    def __str__(self):
        return self.id

    def get_track(self,direction) -> Track:
        return self.tracks[str(direction)]

class Map:
    def __init__(self,tracks,switches):
        self.tracks=tracks
        self.switches=switches
        self.map={}
    
    def get(self,colors) -> Switch:
        return self.switches[colors]

    def check_path(self,train,switch: Switch,direction):
        tim=time.time()
        self._see_part(train,switch.get_track(direction),switch,time)

    def mark_track(self,train,switch,direction):
        switch=map.get(switch)
        switch.get_track(direction).train = train
        
    def _see_part(self,train,track: Track,come_from_sw,ttime):
        if track.is_free_at(ttime):
            next_valto,drtc = track.get_end(come_from_sw)
            if drtc == "-":
                return True
            else:
                return self._see_part(train,next_valto.get_track("-"),next_valto,ttime+track.time)
        else:
            return False
        


tras={}
for tra in timetable:
    tras[tra]=Track(tra,timetable[tra])
sws={}
for swr in data:
    if not((swr[0],swr[1]) in sws):
        sws[(swr[0],swr[1])]=Switch((swr[0],swr[1]),tras[data[swr]],swr[2])
        tras[data[swr]].ends[sws[(swr[0],swr[1])]] = swr[2]

    else:
        sws[(swr[0],swr[1])].tracks[swr[2]]=tras[data[swr]]
        tras[data[swr]].ends[sws[(swr[0],swr[1])]] = swr[2]

map=Map(tras.values(),sws)


def decide(train,at_switch: tuple[str,str]):
    switch=map.get(at_switch)

    posible_to_go=[]

    if switch.get_track('0').is_free_for(train):
        if map.check_path(train,switch,'0'):
            posible_to_go.append('0')

    if switch.get_track('1').is_free_for(train):
        if map.check_path(train,switch,'1'):
            posible_to_go.append('1')

    return posible_to_go

decide("sigma1",)

    

    




    