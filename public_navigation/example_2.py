from collections import defaultdict
import heapq

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

# Create a graph with edge weights = 1 between each neighbor on a route
graph = defaultdict(list)
bus_lookup = defaultdict(list)

for bus, stops in routes.items():
    for i in range(len(stops) - 1):
        a, b = stops[i], stops[i + 1]
        graph[a].append((b, 1, bus))
        graph[b].append((a, 1, bus))  # assume bidirectional
        bus_lookup[(a, b)].append(bus)
        bus_lookup[(b, a)].append(bus)

def shortest_route(start, end):
    heap = [(0, start, [], [])]  # (distance, current_station, path, bus history)
    visited = set()

    while heap:
        dist, station, path, history = heapq.heappop(heap)

        if station == end:
            return path + [station], history

        if station in visited:
            continue
        visited.add(station)

        for neighbor, cost, bus in graph[station]:
            if neighbor not in visited:
                heapq.heappush(
                    heap,
                    (dist + cost,
                     neighbor,
                     path + [station],
                     history + [{bus: [station, neighbor]}])
                )

    return None, None

# Example usage
stations, path = shortest_route("A", "Z")
print("Shortest path based on station hops:")
for p in path:
    bus = list(p.keys())[0]
    start, end = list(p.values())[0]
    print(f"  Take {bus} from {start} to {end}")
