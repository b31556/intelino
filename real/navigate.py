"""
MAP={"sw1":["st1","sw4","st2"],
     "st1":["sw1","sw2"],
     "st2":["sw1","sw2"],
     "sw2":["st2","sw3","st1"],

     "sw3":["st4","sw2","st3"],
     "st3":["sw3","sw4"],
     "st4":["sw3","sw4"],
     "sw4":["st3","sw1","st4"],
     
     }
"""
"""
MAP={"st1":[None,"sw1"],
    "st2":[None,"sw1"],
    "sw1":["st1","st3","st2"],
    "st3":[None,"sw1"]}
"""


import json

with open("intelino/real/map.json","r") as f:
    MAP=json.loads(f.read())

from collections import deque

def route(fro,to, occupation:list[str],last_station=None,lasz_attempt=False):
    if fro==to:
        return [],[],[]
    que = deque([fro])
    visited=set([])
    parent={fro:None}

    sucess=False

    while que:
        node=que.popleft()
        if node == to:
            sucess=True
            break

        if node == None:
            continue

        if node in occupation:
            if not lasz_attempt:
                continue

        neighs=[]

        if len(MAP[node]) == 3:
            if parent.get(node) is None:
                if last_station is not None:
                    if last_station == MAP[node][1]:
                        neighs.append(MAP[node][0])
                        neighs.append(MAP[node][2])
                    else:
                        neighs.append(MAP[node][1])
                else:
                    neighs.append(MAP[node][0])
                    neighs.append(MAP[node][2])
                    neighs.append(MAP[node][1])
            elif parent.get(node) == MAP[node][1]:
                neighs.append(MAP[node][0])
                neighs.append(MAP[node][2])
            else:
                neighs.append(MAP[node][1])

        else:
            if False:
                neighs.append(MAP[node][0])
                neighs.append(MAP[node][1])
            elif parent.get(node) == None:
                neighs.append(MAP[node][0])
                neighs.append(MAP[node][1])
            elif parent.get(node) == MAP[node][0]:
                neighs.append(MAP[node][1])
            else:
                neighs.append(MAP[node][0])





        for neigh in neighs:
            if f"{node}+{neigh}" not in visited:
                visited.add(f"{node}+{neigh}")
                parent[neigh] = node
                que.append(neigh)

    if not sucess:
        if not lasz_attempt:
            return route(fro,to,occupation,last_station,True)

    path=[]
    manual=[]
    current=to
    while current is not None:

        if current in path:
            break
        

        if len(MAP[current]) == 2:
            if current != to:
                manual.append("pass")
            else:
                manual.append("stop")

        if parent.get(current) is not None:
            if len(MAP[parent.get(current)]) == 3:
                if current == MAP[parent.get(current)][0]:
                    manual.append(0)
                if current == MAP[parent.get(current)][2]:
                    manual.append(1)


        path.append(current)
        current=parent.get(current)

    if current is not None:
        return route(fro,parent.get(current),occupation)

    path.reverse()
    manual.reverse()

    for path_elem_index in range(len(path)-1):
        path_elem=path[path_elem_index]
        if path_elem in occupation:
            path=path[:path_elem_index+1:]
            break

    
    manual.pop(0)  ###TODO: REMOVE THIS IF THE STATION IS SHORT AND THE TRAIN MIGHT PASS IT

    direction=(0 if MAP[path[0]][0]==path[1] else 1) if len(MAP[path[0]])==2 else "KYS"

    return manual,direction,path

if __name__ == "__main__":
    print(route("allkulon","st10",[]))