from collections import deque
import json


try:
    with open("intelino/real/map.json","r") as f:
        MAP=json.loads(f.read())
except FileNotFoundError:
    with open("real/map.json","r") as f:
        MAP=json.loads(f.read())


def depth_first_search(fro,to,occupation,last_station):
    if fro==to:
        return [],[],[]
    que = deque([fro])
    visited=set([])
    parent={fro:None}

    sucess=False

    while que:
        node=que.popleft()
        if node in occupation:
            continue

        if node == to:
            sucess=True
            break

        if node == None:
            continue

        

        neighs=[]

        if len(MAP[node]) == 3:
            if parent.get(node) is None:
                if last_station is not None:
                    if last_station == MAP[node][1]:
                        neighs.append(MAP[node][0])
                        neighs.append(MAP[node][2])
                    if last_station == MAP[node][0]:
                        neighs.append(MAP[node][0])
                    if last_station == MAP[node][2]:
                        neighs.append(MAP[node][2])
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
            if neigh not in visited:
                visited.add(neigh)
                parent[neigh] = node
                que.append(neigh)

    if not sucess:
        return [],[]

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

    return path,manual


def route(fro,to, occupation:list[str],last_station=None):
    if fro == to:
        return False,False,False
    path,manual = depth_first_search(fro,to,occupation,last_station)
    path_force,manual_force = depth_first_search(fro,to,[],last_station)

    path.reverse()
    manual.reverse()
    path_force.reverse()
    manual_force.reverse()

    if len(path_force) == 0:
        raise Exception("No path found")
    
    if not path==path_force:
        if False if path_force[1] in occupation else (True if len(path) == 0 else (len(path) - 3 >= len(path_force))):
            path=path_force
            manual=manual_force
            for path_elem_index in range(len(path)-1):
                path_elem=path[path_elem_index]
                if path_elem in occupation:
                    path=path[:path_elem_index:]
                    break
    
    if len(path) == 0 or len(path) == 1:
        return False,False,False
           
    direction=(0 if (MAP[fro][0] == last_station) ^ (MAP[path[0]][0] == path[1]) else 1) if len(MAP[path[0]]) == 2 else (0 if (MAP[fro][1] == last_station) ^ (MAP[path[0]][1] == path[1]) else 1)

    
    manual.pop(0)
    

    return manual,direction,path


if __name__ == "__main__":
    print(route("st1","st10",["sw2"],"sw1"))
  