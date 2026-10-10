import random
import threading
import time

import pytest

import control
import navigate
from fake_track import MAP, fire_marker, run, setup

STATIONS = [n for n, v in MAP.items() if len(v) == 2]
STUBS = [n for n, v in MAP.items() if len(v) == 2 and None in v]


# --- navigate: committed exits and the "do not start" rule -----------------------------------------

def test_route_does_not_start_when_the_exit_after_the_next_node_is_blocked():
    # fo-fo -> fo-kuma -> c-main -> c-2: c-main is taken, the train would pass the fo-kuma split towards it
    assert navigate.route("fo-fo", "c-2", ["c-main"], "fo-mumu") == (False, False, False)


def test_route_still_starts_when_only_a_later_node_is_blocked():
    _, _, path = navigate.route("fo-fo", "c-2", ["c-2"], "fo-mumu")
    assert path[:3] == ["fo-fo", "fo-kuma", "c-main"]


def test_forced_exit_is_the_only_way_on_besides_turning_back():
    _, _, path = navigate.route("b-ki", "fo-1", [], "b-be", forced_exit="fo-ku")
    assert path[1] == "fo-ku"
    _, _, path = navigate.route("b-ki", "fo-1", [], "b-be", forced_exit="fo-kuma")
    assert path[1] == "fo-kuma"
    with pytest.raises(Exception):  # fo-3 is only reachable through fo-kuma
        navigate.route("b-ki", "fo-3", [], "b-be", forced_exit="fo-ku")


def test_committed_nodes_run_to_the_first_switch_where_the_train_may_still_choose():
    assert navigate.committed_nodes(["fo-1", "fo-12", "fo-mumu", "fo-fo", "fo-kuma", "c-main", "c-2"]) == ["fo-mumu"]
    # a-k -> a-1 -> a-m (entered from a branch) -> aa-main (entered from its trunk, open choice)
    assert navigate.committed_nodes(["a-k", "a-1", "a-m", "aa-main", "aa-1"]) == ["a-m", "aa-main"]
    assert navigate.committed_nodes(["fo-3", "fo-34", "fo-fo", "fo-kuma", "c-main", "c-2"]) == ["fo-fo", "fo-kuma"]
    assert navigate.committed_nodes(["fo-fo", "fo-kuma"]) == []


def test_route_does_not_start_when_a_node_it_would_be_committed_to_is_blocked():
    # fo-kuma is committed (fo-fo has no choice), c-main is not, only a train that could still turn away may stop before it
    assert navigate.route("fo-3", "c-2", ["fo-kuma"], "fo-3") == (False, False, False)
    _, _, path = navigate.route("fo-3", "c-2", ["c-main"], "fo-3")
    assert path == ["fo-3", "fo-34", "fo-fo", "fo-kuma"]


def test_passing_places_are_the_stations_on_parallel_tracks():
    assert navigate.passing_places() == {"a-1": ["a-2"], "a-2": ["a-1"]}


def test_route_goes_on_to_a_passing_place_when_the_rest_of_the_stretch_is_blocked():
    # fo-ku -> a-k -> a-1 -> a-m -> aa-main: the train can wait on a-1, the other track stays free
    _, _, path = navigate.route("fo-ku", "aa-1", ["aa-main"], "fo-mumu")
    assert path == ["fo-ku", "a-k", "a-1"]
    # with the other track taken as well nobody could get past it there
    assert navigate.route("fo-ku", "aa-1", ["aa-main", "a-2"], "fo-mumu") == (False, False, False)


def test_route_does_not_start_for_a_destination_somebody_stands_on_when_it_would_be_committed():
    assert navigate.route("fo-kuma", "c-2", ["c-2"], "fo-fo") == (False, False, False)


def test_a_waiting_train_only_keeps_what_it_physically_sits_on(monkeypatch):
    trains, _ = setup(monkeypatch, ["a-1", "fo-mumu"])
    control.COMMITTED_NODES[trains[0]] = ["a-m", "aa-main"]
    control.COMMITTED_NODES[trains[1]] = ["fo-ku", "a-k"]
    control.wait_in_queue(trains[0])  # a station: no split passed, nothing committed
    control.wait_in_queue(trains[1])  # a switch: it is on the exit it already passed the split for
    assert control.COMMITTED_NODES[trains[0]] == []
    assert control.COMMITTED_NODES[trains[1]] == ["fo-ku"]


@pytest.mark.parametrize("destinations", [["aa-1", "fo-2"], ["aa", "fo"]])
def test_trains_going_opposite_ways_pass_each_other_on_a_1_and_a_2(monkeypatch, destinations):
    side_by_side = []
    for seed in range(60):
        def look(trains):
            if {t.at for t in trains} == {"a-1", "a-2"}:
                side_by_side.append(seed)

        trains, problems = run(monkeypatch, ["fo-1", "aa-2"], destinations, seed, on_step=look)
        assert problems == []
        assert not any(t.moving for t in trains), f"seed {seed} did not finish"
        assert control.TRAINS_IN_WATITING_LINE == [], f"seed {seed}: a train is still waiting"
        assert control.POSITION[trains[0]] in ("aa-1", "aa-2") and control.POSITION[trains[1]] in ("fo-1", "fo-2")
    assert side_by_side, "the trains never stood on both tracks of the siding at once"


# --- station groups --------------------------------------------------------------------------------

def test_stubs_are_grouped_by_prefix_and_switches_are_not():
    assert navigate.station_groups() == {"fo": ["fo-1", "fo-2", "fo-3", "fo-4"], "b": ["b-1", "b-2"],
                                         "c": ["c-1", "c-2"], "aa": ["aa-1", "aa-2"]}


def test_pick_from_group_skips_taken_stubs_and_returns_none_when_full():
    assert navigate.pick_from_group("c", "fo-1", "fo-1", ["c-1"], []) == "c-2"
    assert navigate.pick_from_group("c", "fo-1", "fo-1", [], ["c-2"]) == "c-1"
    assert navigate.pick_from_group("c", "fo-1", "fo-1", ["c-1"], ["c-2"]) is None
    assert navigate.pick_from_group("fo", "fo-2", "fo-2", [], []) == "fo-2"  # already standing on one


# --- control: whole runs on the real map -----------------------------------------------------------

def test_claiming_the_committed_exit_stops_the_collision_seen_in_the_simulation(monkeypatch):
    # before the exit was claimed t1 re-planned away from a split it had already passed and hit t0
    for seed in range(40):
        _, problems = run(monkeypatch, ["b-2", "fo-1"], ["fo", "a-1"], seed)
        assert problems == []
        _, problems = run(monkeypatch, ["aa-2", "fo-2"], ["fo", "b"], seed)
        assert problems == []


@pytest.mark.parametrize("trains", [2, 3])
def test_random_runs_never_collide_or_lose_track_of_a_train(monkeypatch, trains):
    for seed in range(150):
        rnd = random.Random(seed)
        starts = rnd.sample(STUBS, trains)
        destinations = [rnd.choice(STATIONS) for _ in range(trains)]
        try:
            _, problems = run(monkeypatch, starts, destinations, seed)
        except Exception as e:  # a destination one train can not reach alone is refused by set_plan, not a bug here
            assert "No path found" in str(e)
            continue
        assert problems == [], f"seed {seed}: {starts} -> {destinations}"


@pytest.mark.parametrize("reserve", [True, False])
def test_other_trains_are_kept_off_the_nodes_a_train_is_committed_to(monkeypatch, reserve):
    monkeypatch.setattr(control, "RESERVE_COMMITTED_NODES", reserve)
    trains, _ = setup(monkeypatch, ["fo-1", "fo-3"])
    control.set_plan(0, "c-2")  # fo-1 -> fo-12 -> fo-mumu: it has started towards fo-12 and holds fo-mumu
    assert control.NEXT_STATION[trains[0]] == "fo-12"
    assert control.COMMITTED_NODES[trains[0]] == ["fo-mumu"]  # fo-mumu is a switch entered from its trunk, the train may still choose there
    taken = control.make_occupation(trains[1])
    assert "fo-12" in taken
    assert ("fo-mumu" in taken) is reserve


def test_a_train_holds_every_node_up_to_the_next_open_choice(monkeypatch):
    # fo-3 -> fo-34 -> fo-fo -> fo-kuma: fo-fo is entered from a branch, so it has no choice but to go on to fo-kuma
    trains, _ = setup(monkeypatch, ["fo-3", "fo-1"])
    control.set_plan(0, "c-2")
    assert control.NEXT_STATION[trains[0]] == "fo-34"
    assert control.COMMITTED_NODES[trains[0]] == ["fo-fo", "fo-kuma"]
    assert {"fo-34", "fo-fo", "fo-kuma"} <= set(control.make_occupation(trains[1]))


def test_trains_sent_to_a_station_take_different_stubs(monkeypatch):
    trains, problems = run(monkeypatch, ["fo-3", "fo-4", "fo-1"], ["c", "c", "fo"], seed=3)
    assert problems == []
    assert {control.POSITION[trains[0]], control.POSITION[trains[1]]} == {"c-1", "c-2"}


def test_a_station_no_stub_of_which_can_be_reached_is_an_error_not_a_silent_wait(monkeypatch):
    setup(monkeypatch, ["b-1"])  # from b-1 the c stubs are not reachable in one plan
    with pytest.raises(Exception, match="No path found"):
        control.set_plan(0, "c")
    assert control.TRAINS_IN_WATITING_LINE == []


def test_a_full_station_makes_the_train_wait_instead(monkeypatch):
    trains, clock = setup(monkeypatch, ["fo-3", "fo-4", "fo-1"])
    control.set_plan(0, "c")
    control.set_plan(1, "c")
    for train in trains[:2]:  # let both arrive
        while train.moving:
            train.arrive()
            fire_marker(train, clock)
    control.set_plan(2, "c")
    assert trains[2] in control.TRAINS_IN_WATITING_LINE and not trains[2].moving


def test_a_waiting_train_is_retried_when_the_blocker_arrives_and_parks(monkeypatch):
    trains, problems = run(monkeypatch, ["fo-1", "fo-2"], ["aa-1", "aa-2"], seed=2)
    assert problems == []
    assert [control.POSITION[t] for t in trains] == ["aa-1", "aa-2"]


def test_check_and_claim_is_one_step_when_two_trains_decide_at_once(monkeypatch):
    trains, _ = setup(monkeypatch, ["fo-1", "fo-2"])
    real_route = navigate.route

    def slow_route(*args, **kwargs):  # widens the gap between checking a node and claiming it
        result = real_route(*args, **kwargs)
        time.sleep(0.05)
        return result

    monkeypatch.setattr(navigate, "route", slow_route)
    threads = [threading.Thread(target=control.set_plan, args=(0, "c-2")),
               threading.Thread(target=control.set_plan, args=(1, "c-1"))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # both trains go through fo-12 first, only one may have claimed it
    assert [control.NEXT_STATION.get(t) for t in trains].count("fo-12") == 1
