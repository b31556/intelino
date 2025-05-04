MAP={"sw1":["st1","kt","st2"],
     "st1":["sw1","sw2"],
     "st2":["sw1","sw2"],
     "sw2":["st2","sw3","st1"],
     
    "kt":["sw1","sw4"],

     "sw3":["st4","sw2","st3"],
     "st3":["sw3","sw4"],
     "st4":["sw3","sw4"],
     "sw4":["st3","kt","st4"],
     
     }

import requests

from collections import deque

def route(fro,to):
    que = deque([fro])
    visited=set([fro])
    parent={fro:None}

    while que:
        node=que.popleft()
        if node == to:
            break

        if node == None:
            continue

        neighs=[]

        if len(MAP[node]) == 3:
            if parent.get(node) == MAP[node][1]:
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
            if neigh not in visited:
                visited.add(neigh)
                parent[neigh] = node
                que.append(neigh)

    path=[]
    manual=[]
    current=to
    while current is not None:

        

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
    path.reverse()
    manual.reverse()

    manual.pop(0)

    direction=(0 if MAP[path[0]][0]==path[1] else 1) if len(MAP[path[0]])==2 else "KYS"

    print(manual)
    print(direction)
    print(path)



    requests.post(f"http://localhost:5080/{0}",json=manual)
    requests.post(f"http://localhost:5080/{0}/{direction}")


    

    return path if path[0] == fro else []   

print(route("st1","st4"))