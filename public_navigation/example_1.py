from collections import deque

routes = {
    "98":    ["A", "B", "C", "D"],
    "161":   ["C", "E", "F", "G", "H"],
    "97E":   ["A", "I", "J", "K", "L", "H"],
    "46":    ["D", "M", "N", "O", "F"],
    "12A":   ["P", "Q", "R", "F", "S", "T"],
    "29B":   ["J", "U", "V", "W", "T"],
    "88":    ["W", "X", "Y", "Z"],
    "100":   ["G", "AA", "AB", "AC", "Z"],
    "69X":   ["L", "AD", "AE", "AF", "AC"],
    "11":    ["AF", "AG", "AH", "AI", "AJ", "Z"],
    "500":   ["R", "K", "M", "V", "AJ"],
}

def get_buses(station):
    for bus in routes:
        if station in routes[bus]:
            yield bus, routes[bus]

def route(fro, to):
    que = deque([[fro, [], []]])
    visited = set()

    while que:
        station, path, bushistory = que.popleft()

        if station == to:
            return path + [station], bushistory

        for bus, route_list in get_buses(station):
            try:
                idx = route_list.index(station)
                # Look both directions from the current station on this route
                for i in range(len(route_list)):
                    if i != idx and route_list[i] not in visited:
                        visited.add(route_list[i])
                        que.append([route_list[i], path + [station], bushistory + [{bus: [station, route_list[i]]}]])
            except ValueError:
                pass

    return False

# example usage
stations, path = route("A", "Z")
print("your path:")
for p in path:
    bus = list(p.keys())[0]
    from_stop, to_stop = list(p.values())[0]
    print(f"  travel with {bus} from {from_stop} to {to_stop}")
