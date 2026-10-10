from collections import deque
import json





def depth_first_search(fro,to,occupation,last_station,forced_exit=None):

    try:
        with open("intelino/real/map.json","r") as f:
            MAP=json.loads(f.read())
    except FileNotFoundError:
        with open("real/map.json","r") as f:
            MAP=json.loads(f.read())
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
                ##? i love niki !

        if node == fro and forced_exit is not None:
            # the train already passed the split, so the only ways out are the exit it is committed to or turning back
            neighs=[n for n in neighs if n in (forced_exit,last_station)]

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

        if parent.get(current) is not None and parent.get(parent.get(current)) is not None:
            if len(MAP[parent.get(current)]) == 3:
                if current == MAP[parent.get(current)][0]:
                    manual.append(0)
                if current == MAP[parent.get(current)][2]:
                    manual.append(1)

        path.append(current)
        current=parent.get(current)

    return path,manual


def _load_map():
    try:
        with open("intelino/real/map.json","r") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        with open("real/map.json","r") as f:
            return json.loads(f.read())


def commit_end(path):
    """Index in `path` of the last node the train can not avoid once it has started towards path[1].
    path[1] is the node it heads to, path[2] the exit it already passed the split for. From there on the train is
    still held on its way by every node that leaves no choice (a station, or a switch entered from a branch)
    and may only change its mind at a switch entered from its trunk, that switch itself is still part of the way."""
    MAP=_load_map()
    last=min(2,len(path)-1)
    while last < len(path)-1:
        node,came=path[last],path[last-1]
        if len(MAP[node]) == 3 and came == MAP[node][1]:   # diverging switch, the exit is still open
            break
        last+=1
    return last


def is_switch(node):
    return len(_load_map()[node]) == 3


def passing_places():
    """Stations on parallel tracks: two or more stations between the same pair of switches (a-1 and a-2).
    A train waiting on one of them leaves the other track free for a train coming the opposite way."""
    between={}
    for node,neighs in _load_map().items():
        if len(neighs) == 2 and None not in neighs:
            between.setdefault(frozenset(neighs),[]).append(node)
    return {node:[o for o in nodes if o != node] for nodes in between.values() if len(nodes) > 1 for node in nodes}


def passing_place_before(path,blocked_index,occupation):
    """Index of the farthest passing place on path[1:blocked_index] where a train can wait for the blocked node.
    The blocked node may be right behind it, that is the switch the other train goes through on the parallel track.
    One parallel track has to be free so the other train can get past. None if there is no such place."""
    places=passing_places()
    for index in range(blocked_index-1,0,-1):
        node=path[index]
        if node in places and any(other not in occupation for other in places[node]):
            return index
    return None


def committed_nodes(path):
    """The nodes after path[1] that the train is committed to, see commit_end"""
    return path[2:commit_end(path)+1]


def station_groups():
    """Dead-end stubs grouped by name prefix: fo-1..fo-4 -> {"fo": [...]}.
    Sending a train to the group name means "any free stub of that station"."""
    MAP=_load_map()
    groups={}
    for node,neighs in MAP.items():
        if len(neighs) == 2 and None in neighs:
            groups.setdefault(node.rsplit("-",1)[0],[]).append(node)
    return groups


def pick_from_group(group,fro,last_station,occupation,reserved,forced_exit=None):
    """Closest stub of `group` that nobody stands on, is heading to or has chosen. None if there is no free one right now, raises if none can be reached at all."""
    members=station_groups()[group]
    if fro in members:
        return fro
    best=None
    for stub in members:
        if stub in occupation or stub in reserved:
            continue
        try:
            plan,direction,path=route(fro,stub,occupation,last_station,forced_exit)
        except Exception:   # not reachable from here
            continue
        if not path:
            continue
        key=(path[-1]!=stub,len(path))   # fully free path first, then shortest
        if best is None or key < best[0]:
            best=(key,stub)
    if best is None:
        for stub in members:   # taken right now is fine (wait), but a station no stub of which can be reached at all is an error like for a single station
            try:
                if route(fro,stub,[],last_station,forced_exit)[2]:
                    return None
            except Exception:
                continue
        raise Exception(f"No path found to station {group}")
    return best[1]


def route(fro,to, occupation:list[str],last_station=None,forced_exit=None):
    try:
        with open("intelino/real/map.json","r") as f:
            MAP=json.loads(f.read())
    except FileNotFoundError:
        with open("real/map.json","r") as f:
            MAP=json.loads(f.read())
    if fro == to:
        return False,False,False
    path,manual = depth_first_search(fro,to,occupation,last_station,forced_exit)
    path_force,manual_force = depth_first_search(fro,to,[],last_station,forced_exit)

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
            committed=commit_end(path)
            for path_elem_index in range(len(path)):   # the destination too, a train must not start for a destination somebody stands on
                path_elem=path[path_elem_index]
                if path_elem in occupation:
                    if path_elem_index <= committed:
                        # the train could not turn away from the blocked node any more once it started: only start if there is a passing place to wait on
                        wait_at=passing_place_before(path,path_elem_index,occupation)
                        if wait_at is None:
                            return False,False,False
                        path=path[:wait_at+1]
                        break
                    path=path[:path_elem_index:]
                    break
    
    if len(path) == 0 or len(path) == 1:
        return False,False,False

    direction=(0 if (MAP[fro][0] == last_station) ^ (MAP[path[0]][0] == path[1]) else 1) if len(MAP[path[0]]) == 2 else (0 if (MAP[fro][1] == last_station) ^ (MAP[path[0]][1] == path[1]) else 1)

    #manual.pop(0)
    

    return manual,direction,path


if __name__ == "__main__":
    print(route("fo-34","c-2",[],None))
  