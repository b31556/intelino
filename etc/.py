from heapq import heappush, heappop
from math import inf

Time = float

class Interval:
    def __init__(self, start: Time, end: Time, train_id: int):
        self.start = start
        self.end = end
        self.train_id = train_id

    def __lt__(self, other):
        return self.start < other.start

class TrackReservation:
    def __init__(self):
        self.reservations = []  # List of Interval objects

    def reserve(self, start: Time, end: Time, train_id: int):
        self.reservations.append(Interval(start, end, train_id))
        self.reservations.sort()  # Sort by start time

    def earliest_available(self, arrival: Time, duration: Time, train_id: int) -> Time:
        t = arrival
        i = 0
        while i < len(self.reservations) and self.reservations[i].start < arrival:
            if self.reservations[i].end > t:
                t = self.reservations[i].end  # Wait until this reservation ends
            i += 1

        while i < len(self.reservations):
            if t + duration <= self.reservations[i].start:
                return t  # Found a gap
            t = self.reservations[i].end
            i += 1
        return t

def time_dependent_dijkstra(graph: list[list[tuple[int, Time]]], start: int, dest: int,
                           reservations: list[TrackReservation], departure_time: Time = 0.0,
                           train_id: int = 0) -> tuple[list[int], list[tuple[Time, Time]]]:
    n = len(graph)
    dist = [inf] * n
    prev = [-1] * n
    times = [None] * n  # Store (start, end) times for each node
    pq = []  # (time, node)

    dist[start] = departure_time
    times[start] = (departure_time, departure_time)  # Start node has no wait
    heappush(pq, (departure_time, start))

    while pq:
        t_u, u = heappop(pq)
        if t_u > dist[u]:
            continue
        if u == dest:
            break

        for v, d_e in graph[u]:
            t_start = reservations[u].earliest_available(t_u, d_e, train_id)
            t_v = t_start + d_e

            if t_v < dist[v]:
                dist[v] = t_v
                prev[v] = u
                times[v] = (t_start, t_v)
                heappush(pq, (t_v, v))

    # Reconstruct path and times
    path = []
    path_times = []
    at = dest
    while at != -1:
        path.append(at)
        if times[at] is not None:
            path_times.append(times[at])
        at = prev[at]
    path = path[::-1]
    path_times = path_times[::-1] if path_times else [(departure_time, departure_time)]
    return path, path_times

def schedule_train(train_id: int, start: int, dest: int, graph: list[list[tuple[int, Time]]],
                  reservations: list[TrackReservation], departure_time: Time = 0.0):
    path, path_times = time_dependent_dijkstra(graph, start, dest, reservations, departure_time, train_id)
    if not path:
        print(f"Train {train_id} from {start} to {dest}: No path")
        return

    # Reserve tracks and build detailed output
    current_time = departure_time
    segments = []
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        d_e = next(edge[1] for edge in graph[u] if edge[0] == v)
        t_start = reservations[u].earliest_available(current_time, d_e, train_id)
        t_end = t_start + d_e
        reservations[u].reserve(t_start, t_end, train_id)
        segments.append((u, v, t_start, t_end))
        current_time = t_end

    # Print detailed schedule
    print(f"Train {train_id} from {start} to {dest}:")
    print(f"  Path: {' -> '.join(map(str, path))}")
    for u, v, t_s, t_e in segments:
        print(f"  Track {u} -> {v}: {t_s:.1f} to {t_e:.1f}")
    return segments

def main():
    n = 15
    graph = [[] for _ in range(n)]

    graph[0].append((7, 1))
    graph[1].append((5, 1))
    graph[2].append((6, 1))
    graph[3].append((6, 1))
    graph[7].append((9, 1))
    graph[5].append((7, 1))
    graph[6].append((8, 1))
    graph[8].append((10, 1))
    graph[5].append((8, 1))
    graph[10].append((13, 1))
    graph[10].append((14, 1))
    graph[9].append((12, 1))
    graph[9].append((11, 1))

    crtr={}

    crtr[0]={7:}












    reservations = [TrackReservation() for _ in range(n)]

    # Schedule your trains
    train1_t = schedule_train(1, 0, 11, graph, reservations, 0.0)  # Train 1: 0 to 4
    train2_t = schedule_train(2, 1, 14, graph, reservations, 0.0)  # Train 2: 1 to 3
    train3_t = schedule_train(3, 2, 13, graph, reservations, 0.0)  # Train 3: 2 to 3


    

    now=0
    while True:
        print(f"clock: {now}")
        try:
            if now == train1_t[0][3]:
                print(f"train1 is arriving at {train1_t[0][1]}")
                train1_t.pop(0)
            if now == train1_t[0][2]:
                print(f"train1 is departing from {train1_t[0][0]}")
            
        except IndexError:
            pass

        try:
            if now == train2_t[0][3]:
                print(f"train2 is arriving at {train2_t[0][1]}")
                train2_t.pop(0)
            if now == train2_t[0][2]:
                print(f"train2 is departing from {train2_t[0][0]}")
            
        except IndexError:
            pass

        try:
            if now == train3_t[0][3]:
                print(f"train3 is arriving at {train3_t[0][1]}")
                train3_t.pop(0)
            if now == train3_t[0][2]:
                print(f"train3 is departing from {train3_t[0][0]}")
            if now == train3_t[0][3]:
                print(f"train3 is arriving at {train3_t[0][1]}")
                train3_t.pop(0)
        except IndexError:
            pass

        now+=1
        input()


if __name__ == "__main__":
    main()