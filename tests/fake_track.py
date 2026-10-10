"""Fake trains on the real map.json, driving the real control.py handlers.

Model: a train passes a node's split first and then reads its marker, so the exit of a node is fixed
by the steering decision set one marker earlier. A train that is told to stop stays on that exit."""
import json
import random
import types

import control
from intelino.trainlib.enums import MovementDirection as MD
from intelino.trainlib.enums import SnapColorValue as C
from intelino.trainlib.enums import SteeringDecision as SD

MAP = json.load(open("real/map.json"))


class FakeClock:
    now = 1000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        pass


class FakeTrain:
    def __init__(self, index, node):
        self.id, self.alias = index, f"t{index}"
        self.at, self.came, self.target = node, None, None
        self.moving, self.heading_forward, self.steer = False, None, SD.LEFT
        self.battery, self.speed, self.colors = 100, 0, None

    def _exit(self):
        m = MAP[self.at]
        if len(m) == 3:
            return (m[0] if self.steer == SD.LEFT else m[2]) if self.came == m[1] else m[1]
        if self.came is None:
            return [n for n in m if n][0]
        return m[1] if self.came == m[0] else m[0]

    def drive_at_speed(self, speed, direction):
        if self.heading_forward is None:
            self.heading_forward, self.target = direction != MD.BACKWARD, self._exit()
        else:
            now_forward = (not self.heading_forward) if direction == MD.INVERT else direction == MD.FORWARD
            if now_forward != self.heading_forward:
                self.came, self.target = self.target, self.came
            self.heading_forward = now_forward
        self.moving = True

    def stop_driving(self):
        self.moving = False

    def set_next_split_steering_decision(self, decision):
        self.steer = decision

    def arrive(self):
        self.came, self.at = self.at, self.target
        self.target = self._exit()


def setup(monkeypatch, starts):
    clock = FakeClock()
    monkeypatch.setattr(control, "time", types.SimpleNamespace(time=clock.time, sleep=clock.sleep))
    for state in (control.POSITION, control.LAST_STATTION, control.DESTINATION, control.NEXT_STATION, control.MOVEMENT_DIRECTION,
                  control.IMMUNITY, control.DESTINATION_GROUP, control.COMMITTED_NODES):
        state.clear()
    control.TRAINS_IN_WATITING_LINE.clear()
    trains = [FakeTrain(i, node) for i, node in enumerate(starts)]
    for train, node in zip(trains, starts):
        control.POSITION[train] = control.LAST_STATTION[train] = node
        control.MOVEMENT_DIRECTION[train] = False
    control.trains[:] = trains
    return trains, clock


def fire_marker(train, clock):
    clock.now += 3
    if len(MAP[train.at]) == 3:
        control.handle_color_change(train, types.SimpleNamespace(color=C.CYAN))
    else:
        control.handle_station(train, types.SimpleNamespace(colors=(C.WHITE, C.MAGENTA, C.WHITE)))


def run(monkeypatch, starts, destinations, seed=0, max_steps=400, on_step=None):
    """Sends every train to its destination, lets them move in a random interleaving.
    Returns (trains, problems) - problems lists collisions and control losing track of a train.
    on_step(trains) is called after every marker, to look at where the trains are."""
    trains, clock = setup(monkeypatch, starts)
    rnd, problems = random.Random(seed), []
    for index, destination in enumerate(destinations):
        control.set_plan(index, destination)
    for _ in range(max_steps):
        moving = [t for t in trains if t.moving]
        if not moving:
            break
        train = rnd.choice(moving)
        train.arrive()
        fire_marker(train, clock)
        if control.POSITION[train] != train.at:
            problems.append(f"{train.alias} is on {train.at} but control thinks {control.POSITION[train]}")
        for other in trains:
            if other is not train and other.at == train.at:
                problems.append(f"{train.alias} and {other.alias} both on {train.at}")
        if on_step:
            on_step(trains)
    return trains, problems
