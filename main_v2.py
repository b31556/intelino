import pygame
import json
import time
from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import SnapColorValue as C, SteeringDecision

# Load map and timetable (adjust filenames as needed)
with open("map.json", "r") as f:
    MAP_DATA = json.load(f)  # e.g., {"BY0":0, "BY1":1, "BR-":0, ...}
with open("timetable.json", "r") as f:
    TIMETABLE = json.load(f)  # Assuming this exists for reservations

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Train System Visualization")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)  # Background
BLACK = (0, 0, 0)       # Free track
RED = (255, 0, 0)       # Reserved track or train 1
BLUE = (0, 0, 255)      # Train 2

# Zone class for managing reservations
class Zone:
    def __init__(self, id):
        self.id = id
        self.reservations = []  # List of (start_time, end_time, train_id)

    def is_reserved(self, current_time):
        for start, end, _ in self.reservations:
            if start <= current_time <= end:
                return True
        return False

# Initialize zones from map_data
ZONES = {zone_id: Zone(zone_id) for zone_id in set(MAP_DATA.values())}

# TrainController class with visualization
class TrainController:
    def __init__(self, train, color):
        self.train = train
        self.color = color
        self.current_key = None
        self.current_zone = None
        self.last_colors = []  # Track last detected colors

    def on_color_detected(self, train, msg):
        """Handle color detection events."""
        color = msg.color
        self.last_colors.append(color)
        if len(self.last_colors) > 3:
            self.last_colors.pop(0)
        if len(self.last_colors) == 3:
            key = self.colors_to_key(self.last_colors)
            if key in MAP_DATA:
                self.current_key = key
                self.current_zone = MAP_DATA[key]
                print(f"Train {self.train.id} at zone {self.current_zone} via key {key}")
            else:
                print(f"Unknown key {key} detected by Train {self.train.id}")

    def colors_to_key(self, colors):
        """Convert a sequence of 3 colors to a map key."""
        color_map = {
            C.BLUE: "B", C.YELLOW: "Y", C.RED: "R", C.WHITE: "W", C.GREEN: "G",
            C.MAGENTA: "0", C.CYAN: "1", C.BLACK: "-"
        }
        return "".join(color_map.get(color, "?") for color in colors)

    def draw(self, screen):
        """Draw the train on the screen."""
        if self.current_key and self.current_key in key_positions:
            pos = key_positions[self.current_key]
            pygame.draw.circle(screen, self.color, pos, 10)

# Define base positions for each zone
zone_positions = {
    0: (100, 100), 1: (200, 100), 2: (300, 100),
    10: (400, 100), 33: (500, 100), 88: (600, 100)
}

# Group keys by zone and assign positions
from collections import defaultdict
zone_keys = defaultdict(list)
for key, zone in MAP_DATA.items():
    zone_keys[zone].append(key)

key_positions = {}
for zone, keys in zone_keys.items():
    base_x, base_y = zone_positions[zone]
    offsets = [-10, 10] if len(keys) == 2 else [0]  # Adjust for more keys if needed
    for i, key in enumerate(keys):
        key_positions[key] = (base_x + offsets[i], base_y)

# Draw the track with reservation status
def draw_track(screen):
    """Draw track points colored by reservation status."""
    current_time = time.time()
    for key, zone_id in MAP_DATA.items():
        zone = ZONES[zone_id]

        color = RED if zone.is_reserved(current_time) else BLACK
        pos = key_positions[key]
        pygame.draw.circle(screen, color, pos, 5)

# Main function
def main():
    # Set up trains (assuming 2 trains)
    trains = TrainScanner(timeout=4.0).get_trains(2)
    controllers = []
    colors = [RED, BLUE]
    for i, train in enumerate(trains):
        controller = TrainController(train, colors[i])
        train.add_front_color_change_listener(controller.on_color_detected)
        train.set_snap_command_execution(False)  # Disable default snap actions
        train.set_snap_command_feedback(False, False)
        train.drive_at_speed(50)  # Start moving
        controllers.append(controller)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear screen
        screen.fill(WHITE)

        # Draw track and trains
        draw_track(screen)
        for controller in controllers:
            controller.draw(screen)

        # Update display
        pygame.display.flip()
        clock.tick(30)  # 30 FPS

    # Cleanup
    for controller in controllers:
        controller.train.stop_driving()
        controller.train.disconnect()
    pygame.quit()

if __name__ == "__main__":
    main()