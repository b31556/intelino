MAP={"sw1":["st1","kt","st2"],
     "st1":["sw1","sw2"],
     "st2":["sw1","sw2"],
     "sw2":["st2","sw3","st1"],
     
    "kt":["sw1","sw4","stX"],

        "stX":["kt",None],

     "sw3":["st4","sw2","st3"],
     "st3":["sw3","sw4"],
     "st4":["sw3","sw4"],
     "sw4":["st3","kt","st4"],
     
     }
"""
MAP={"st1":[None,"sw1"],
    "st2":[None,"sw1"],
    "sw1":["st1","st3","st2"],
    "st3":[None,"sw1"]}
"""

import requests

from collections import deque

def route(fro,to, occupation:list[str]):
    que = deque([fro])
    visited=set([])
    parent={fro:None}

    while que:
        node=que.popleft()
        if node == to:
            break

        if node == None:
            continue

        if node in occupation:
            continue

        neighs=[]

        if len(MAP[node]) == 3:
            if parent.get(node) == MAP[node][1]:
                neighs.append(MAP[node][0])
                neighs.append(MAP[node][2])
            else:
                neighs.append(MAP[node][1])

        else:
            if True:
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

    if MAP[path[0]][0]==path[1]:
        manual.pop(0)

    direction=(0 if MAP[path[0]][0]==path[1] else 1) if len(MAP[path[0]])==2 else "KYS"

    return manual,direction,path

if __name__ == "__main__":
    import time
    start = time.time()
    for i in range(10000):
        route("st1","st2",[])
    print(route("sw3","stX",["sw1"]))
     
    print("made 10 000 planning; Time taken:", time.time()-start)