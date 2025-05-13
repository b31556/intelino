import heapq

# routes = {
#     "161": ["A", "B", "C", "D", "E"],
#     "97E": ["A", "E"],
#     "46": ["C", "D","E"]
# }
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

### Show the routes with different bus colors
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib

G = nx.MultiGraph()  # Use MultiGraph to allow parallel edges
for bus, stops in routes.items():
    for i in range(len(stops) - 1):
        G.add_edge(stops[i], stops[i + 1], weight=1, bus=bus)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=200, node_color="skyblue", font_size=5, font_weight="bold")

# Assign unique colors to each bus route
colors = plt.cm.tab20(range(len(routes)))
bus_colors = {bus: colors[i] for i, bus in enumerate(routes)}

for bus, stops in routes.items():
    edges = [(stops[i], stops[i + 1]) for i in range(len(stops) - 1)]
    nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=[bus_colors[bus]], width=2, alpha=0.7, connectionstyle="arc3,rad=0.2")

plt.savefig("bus_routes_colored.png", dpi=300)


# make the bus routes circular
for route in routes:
    route_extension=routes[route].copy()
    route_extension.reverse()
    route_extension=route_extension[1:]
    routes[route].extend(route_extension)
departures = {
    "98": list(range(0, 60, 5)),
    "161": [3, 18, 33, 48],
    "97E": [10, 30, 50],
    "46": [5, 15, 25, 40],
    "12A": [0, 12, 24, 36, 48],
    "29B": [7, 22, 37],
    "88": [0, 20, 40],
    "100": [10, 30, 50],
    "69X": [6, 21, 36],
    "11": [15, 35, 55],
    "500": [8, 28, 48],
}
# Extend the departure times for 5 hours
for cc in range(1,6):
    for bus in departures:
        depi=departures[bus].copy()
        for a in depi:
            departures[bus].extend([60*cc+a])
timings = {
    "98": [0, 1, 2, 3],
    "161": [0, 2, 4, 6, 8],
    "97E": [0, 2, 4, 6, 8, 10],
    "46": [0, 2, 3, 5, 7],
    "12A": [0, 2, 4, 6, 8, 10],
    "29B": [0, 2, 4, 6, 8],
    "88": [0, 2, 4, 5],
    "100": [0, 3, 5, 8, 10],
    "69X": [0, 2, 4, 6, 8],
    "11": [0, 2, 4, 6, 8, 10],
    "500": [0, 3, 5, 7, 10],
}
# help make the bus routes circular
for bus in timings:
    times_extension=timings[bus].copy()
    for time_index in range(len(times_extension)):
        times_extension[time_index]+=timings[bus][-1]
    times_extension=times_extension[1:]
    timings[bus].extend(times_extension)      


def get_buses(station,time):
    for bus,path in routes.items():
        if station in path:
            for departure in departures[bus]:
                arrival = departure + timings[bus][path.index(station)]
                if arrival >= time:
                    yield arrival - time, bus
                    break

def shortest_route(strttime,start, end):
    heap = [(strttime, start, [], [])]  # (distance, current_station, path, bus history)
    visited = set()
    time=strttime
    while heap:
        time, station, path, history = heapq.heappop(heap)

        if station == end:
            return path + [station], history, time-strttime

        if station in visited:
            continue
        visited.add(station)

        for arrival, bus in get_buses(station,time):
            for stop in routes[bus][routes[bus].index(station)+1:]:   
                if stop not in visited:
                    cost=abs(timings[bus][routes[bus].index(stop)] - timings[bus][routes[bus].index(station)])
                    heapq.heappush(
                        heap,
                        (time + arrival + cost,
                        stop,
                        path + [station],
                        history + [{bus: {station: time + arrival, stop: time+ arrival+cost}}])
                    )

    return None, [], None

# Example usage
stations, path, timetaken = shortest_route(20, "A", "Z")
print("Shortest path based on station hops:")
for p in path:
    bus = list(p.keys())[0]
    start, end = list(p.values())[0].items()
    print(f"  Take {bus} from {start} to {end}")
print(f"you arrive in {timetaken} minutes")
