from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
import random
import time
from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import SnapColorValue as C, SteeringDecision
from intelino.trainlib.messages import TrainMsgEventSnapCommandDetected

@dataclass
class TrainState:
    """Represents the current state of a train"""
    colors: List[str]
    last_position: Optional[Tuple[str, str, str]] = None
    is_in_danger_zone: bool = False

class TrainController:
    def __init__(self):
        # State management
        self.trains: Dict[Train, TrainState] = {}
        self.waiting_trains: List[Train] = []
        self.zones: Dict[str, Train] = {}
        self.danger_zones: Dict[str, Train] = {}
        self.danger_zone_waiting: Dict[str, List[Train]] = {}
        self.track_map: Dict[Tuple[str, str, str], str] = {}
        
        # Load configuration
        self._load_configuration()
        
    def _load_configuration(self):
        """Load track map and timetable from JSON files"""
        with open("timetable.json") as f:
            self.timetable = json.load(f)
            
        with open("map.json", "r") as f:
            track_data = json.load(f)
            for zone in track_data:
                self.track_map[(zone[0], zone[1], zone[2])] = track_data[zone]
                
    def _color_to_code(self, color: C) -> str:
        """Convert color enum to single-letter code"""
        color_map = {
            C.GREEN: "G",
            C.RED: "R",
            C.BLUE: "B",
            C.YELLOW: "Y",
            C.MAGENTA: "M",
            C.WHITE: "W",
            C.CYAN: "C"
        }
        return color_map.get(color, "X")
        
    def _find_next_section(self, current_pos: Tuple[str, str, str]) -> Tuple[str, str, str]:
        """Find the next possible track section"""
        possible_sections = []
        for section in self.track_map:
            if self.track_map[section] == self.track_map[current_pos]:
                possible_sections.append(section)
        possible_sections.remove(current_pos)
        return possible_sections[0]
        
    def _is_path_safe(self, position: Tuple[str, str, str], timestamp: float) -> bool:
        """Check if a path is safe to take"""
        next_section = self._find_next_section(position)
        
        if next_section[2] == "-":
            # Check if next section is available
            next_zone = (next_section[0], next_section[1], "1")
            return (next_zone not in self.track_map or 
                   self._can_enter_zone(next_zone, timestamp + self.timetable[next_zone]))
        else:
            # Recursive check for switch sections
            switch_section = (next_section[0], next_section[1], "-")
            return (self.track_map[switch_section] not in self.track_map or 
                   self._is_path_safe(switch_section, timestamp))
                   
    def _can_enter_zone(self, zone: Tuple[str, str, str], timestamp: float) -> bool:
        """Check if a train can enter a specific zone"""
        return zone not in self.track_map or timestamp > self.timetable.get(zone, 0)
        
    def _mark_path(self, train: Train, position: Tuple[str, str, str], 
                  is_start: bool = False, timestamp: float = None) -> bool:
        """Mark a path as being used by a train"""
        if timestamp is None:
            timestamp = time.time()
            
        if not is_start:
            self.track_map[self.track_map[position]] = train
            
        next_section = self._find_next_section(position)
        
        if next_section[2] == "-":
            # Check if next section is available
            return (not (next_section[0], next_section[1], "0") in self.track_map and 
                   not (next_section[0], next_section[1], "1") in self.track_map)
        else:
            # Check switch sections
            switch_section = (next_section[0], next_section[1], "-")
            return (self.track_map[switch_section] not in self.track_map or 
                   self._mark_path(train, switch_section, False, timestamp))
                   
    def _make_decision(self, train: Train, position: Tuple[str, str, str]) -> str:
        """Make a decision about which direction to take at a switch"""
        possibilities = []
        
        # Check left path
        left_path = (position[1], position[2], "0")
        if (self.track_map[left_path] not in self.track_map and 
            self._is_path_safe(left_path, time.time())):
            possibilities.append("0")
            
        # Check right path
        right_path = (position[1], position[2], "1")
        if (self.track_map[right_path] not in self.track_map and 
            self._is_path_safe(right_path, time.time())):
            possibilities.append("1")
            
        if not possibilities:
            train.stop_driving()
            print("ERROR: No safe path available")
            return "0"
            
        decision = random.choice(possibilities)
        self._mark_path(train, (position[1], position[2], decision))
        return decision
        
    def _handle_color_detection(self, train: Train, msg: TrainMsgEventSnapCommandDetected):
        """Handle color marker detection from train sensors"""
        if msg.color == C.BLACK:
            if train in self.trains:
                train_state = self.trains[train]
                if train_state.colors == ["M"]:
                    # Clear previous path
                    for section in list(self.track_map.keys()):
                        if self.track_map[section] == train:
                            del self.track_map[section]
                            
                    # Make new decision
                    next_pos = self._find_next_section(train_state.last_position)
                    decision = self._make_decision(train, ("C", next_pos[0], next_pos[1]))
                    train.set_next_split_steering_decision(
                        SteeringDecision.LEFT if decision == "0" else SteeringDecision.RIGHT
                    )
                del self.trains[train]
            return
            
        # Handle other colors
        if train not in self.trains:
            self.trains[train] = TrainState(colors=[self._color_to_code(msg.color)])
            return
            
        train_state = self.trains[train]
        train_state.colors.append(self._color_to_code(msg.color))
        
        if len(train_state.colors) >= 3:
            self._process_command(train, train_state.colors)
            
    def _process_command(self, train: Train, colors: List[str]):
        """Process commands based on detected color patterns"""
        # Handle crossing zones (White-Color-White pattern)
        if colors[0] == "W" and colors[2] == "W":
            zone_id = colors[1]
            if zone_id in self.danger_zones:
                if self.danger_zones[zone_id] == train:
                    del self.danger_zones[zone_id]
                    # Start next waiting train if any
                    if zone_id in self.danger_zone_waiting and self.danger_zone_waiting[zone_id]:
                        next_train = self.danger_zone_waiting[zone_id].pop(0)
                        next_train.drive_at_speed(50)
                        self.danger_zones[zone_id] = next_train
                else:
                    # Add train to waiting queue
                    train.stop_driving()
                    if zone_id not in self.danger_zone_waiting:
                        self.danger_zone_waiting[zone_id] = []
                    self.danger_zone_waiting[zone_id].append(train)
            else:
                self.danger_zones[zone_id] = train
                
        # Handle switch points (Cyan-Color-Color pattern)
        if colors[2] == "C":
            # Clear previous path
            for section in list(self.track_map.keys()):
                if self.track_map[section] == train:
                    del self.track_map[section]
                    
            # Update position
            zone = self.track_map[(colors[1], colors[0], "-")]
            if zone in self.track_map:
                train.stop_driving()
            self.track_map[zone] = train
            self.trains[train].last_position = (colors[1], colors[0], "-")
            
        if colors[0] == "C":
            # Clear previous path
            for section in list(self.track_map.keys()):
                if self.track_map[section] == train:
                    del self.track_map[section]
                    
            # Make new decision
            decision = self._make_decision(train, colors)
            zone = self.track_map[(colors[1], colors[2], decision)]
            self.track_map[zone] = train
            self.trains[train].last_position = (colors[1], colors[2], decision)
            
    def run(self):
        """Main control loop"""
        scanner = TrainScanner(timeout=4.0)
        trains = scanner.get_trains(2)  # Get 2 trains
        
        for train in trains:
            train.add_front_color_change_listener(
                lambda t, msg: self._handle_color_detection(t, msg)
            )
            train.set_snap_command_execution(False)  # Disable default snap actions
            train.set_snap_command_feedback(False, False)  # Disable feedback
            train.drive_at_speed(50)
            
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            for train in trains:
                train.stop_driving()
                train.disconnect()

if __name__ == "__main__":
    controller = TrainController()
    controller.run() 