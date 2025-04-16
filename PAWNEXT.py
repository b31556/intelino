import pygame
import asyncio
import platform
import json
import io
import base64
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Train Switch Editor")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Switch and Station properties
SWITCH_WIDTH = 80
SWITCH_HEIGHT = 30
STATION_WIDTH = 60
STATION_HEIGHT = 40
CONNECTION_POINT_RADIUS = 5
CONNECTION_HITBOX_RADIUS = 15
DIVERGING_OFFSET_X = 30
DIVERGING_OFFSET_Y = 20

# Font
font = pygame.font.SysFont("arial", 20)

class Switch:
    def __init__(self, x, y, id):
        self.x = x
        self.y = y
        self.id = id
        self.rect = pygame.Rect(x - SWITCH_WIDTH // 2, y - SWITCH_HEIGHT // 2, SWITCH_WIDTH, SWITCH_HEIGHT)
        self.input_point = (x - SWITCH_WIDTH // 2, y)
        self.straight_point = (x + SWITCH_WIDTH // 2, y)
        self.diverging_point = (x + SWITCH_WIDTH // 2 + DIVERGING_OFFSET_X, y + DIVERGING_OFFSET_Y)

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        pygame.draw.circle(screen, RED, self.input_point, CONNECTION_POINT_RADIUS)
        pygame.draw.circle(screen, RED, self.straight_point, CONNECTION_POINT_RADIUS)
        pygame.draw.circle(screen, RED, self.diverging_point, CONNECTION_POINT_RADIUS)
        pygame.draw.line(screen, BLACK, self.input_point, self.straight_point, 2)
        pygame.draw.line(screen, BLACK, self.input_point, self.diverging_point, 2)
        label = font.render(f"S{self.id}", True, BLACK)
        screen.blit(label, (self.x - 10, self.y - 10))

    def is_over_point(self, pos, point_type):
        point = {
            "input": self.input_point,
            "straight": self.straight_point,
            "diverging": self.diverging_point
        }[point_type]
        return ((pos[0] - point[0]) ** 2 + (pos[1] - point[1]) ** 2) < CONNECTION_HITBOX_RADIUS ** 2

class Station:
    def __init__(self, x, y, id, rotation=0):
        self.x = x
        self.y = y
        self.id = id
        self.rotation = rotation  # 0 or 90 degrees
        self.update_rect_and_points()

    def update_rect_and_points(self):
        if self.rotation == 0:
            self.rect = pygame.Rect(self.x - STATION_WIDTH // 2, self.y - STATION_HEIGHT // 2, STATION_WIDTH, STATION_HEIGHT)
            self.left_point = (self.x - STATION_WIDTH // 2, self.y)
            self.right_point = (self.x + STATION_WIDTH // 2, self.y)
        else:  # 90 degrees
            self.rect = pygame.Rect(self.x - STATION_HEIGHT // 2, self.y - STATION_WIDTH // 2, STATION_HEIGHT, STATION_WIDTH)
            self.left_point = (self.x, self.y - STATION_WIDTH // 2)
            self.right_point = (self.x, self.y + STATION_WIDTH // 2)

    def draw(self, screen):
        # Draw rotated rectangle
        surface = pygame.Surface((STATION_WIDTH, STATION_HEIGHT), pygame.SRCALPHA)
        surface.fill(GREEN)
        rotated_surface = pygame.transform.rotate(surface, self.rotation)
        rect = rotated_surface.get_rect(center=(self.x, self.y))
        screen.blit(rotated_surface, rect.topleft)
        # Draw connection points
        pygame.draw.circle(screen, RED, self.left_point, CONNECTION_POINT_RADIUS)
        pygame.draw.circle(screen, RED, self.right_point, CONNECTION_POINT_RADIUS)
        label = font.render(f"ST{self.id}", True, BLACK)
        screen.blit(label, (self.x - 15, self.y - 10))

    def is_over_point(self, pos, point_type):
        point = {"left": self.left_point, "right": self.right_point}[point_type]
        return ((pos[0] - point[0]) ** 2 + (pos[1] - point[1]) ** 2) < CONNECTION_HITBOX_RADIUS ** 2

class Connection:
    def __init__(self, obj1, point1, obj2, point2, intermediate_points=None):
        self.obj1 = obj1
        self.point1 = point1
        self.obj2 = obj2
        self.point2 = point2
        self.intermediate_points = intermediate_points or []

    def draw(self, screen):
        start_point = {
            "input": self.obj1.input_point if isinstance(self.obj1, Switch) else self.obj1.left_point,
            "straight": getattr(self.obj1, "straight_point", None),
            "diverging": getattr(self.obj1, "diverging_point", None),
            "left": self.obj1.left_point if isinstance(self.obj1, Station) else None,
            "right": self.obj1.right_point if isinstance(self.obj1, Station) else None
        }[self.point1]
        end_point = {
            "input": self.obj2.input_point if isinstance(self.obj2, Switch) else self.obj2.left_point,
            "straight": getattr(self.obj2, "straight_point", None),
            "diverging": getattr(self.obj2, "diverging_point", None),
            "left": self.obj2.left_point if isinstance(self.obj2, Station) else None,
            "right": self.obj2.right_point if isinstance(self.obj2, Station) else None
        }[self.point2]
        if start_point and end_point:
            points = [start_point] + self.intermediate_points + [end_point]
            pygame.draw.lines(screen, BLACK, False, points, 2)

# Game state
switches = []
stations = []
connections = []
selected_obj = None
dragging = False
connecting = False
start_obj = None
start_point = None
temp_points = []
next_switch_id = 1
next_station_id = 1
running = True
FPS = 60

def setup():
    global switches, stations, connections, next_switch_id, next_station_id
    switches = []
    stations = []
    connections = []
    next_switch_id = 1
    next_station_id = 1
    screen.fill(WHITE)

def save_layout():
    layout = {
        "switches": [{"id": s.id, "x": s.x, "y": s.y} for s in switches],
        "stations": [{"id": s.id, "x": s.x, "y": s.y, "rotation": s.rotation} for s in stations],
        "connections": [
            {
                "obj1_id": c.obj1.id,
                "obj1_type": "switch" if isinstance(c.obj1, Switch) else "station",
                "point1": c.point1,
                "obj2_id": c.obj2.id,
                "obj2_type": "switch" if isinstance(c.obj2, Switch) else "station",
                "point2": c.point2,
                "intermediate_points": c.intermediate_points
            }
            for c in connections
        ]
    }
    json_str = json.dumps(layout)
    encoded = base64.b64encode(json_str.encode()).decode()
    return encoded

async def update_loop():
    global selected_obj, dragging, connecting, start_obj, start_point, temp_points, next_switch_id, next_station_id, running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if event.button == 1:  # Left click
                if connecting:
                    # Add intermediate point while connecting
                    temp_points.append(pos)
                else:
                    # Check if clicking a switch or station to drag
                    for obj in switches + stations:
                        if obj.rect.collidepoint(pos):
                            selected_obj = obj
                            dragging = True
                            break
                    else:
                        # Check if clicking a connection point to start connecting
                        for obj in switches + stations:
                            point_types = ["input", "straight", "diverging"] if isinstance(obj, Switch) else ["left", "right"]
                            for point_type in point_types:
                                if obj.is_over_point(pos, point_type):
                                    connecting = True
                                    start_obj = obj
                                    start_point = point_type
                                    temp_points = []
                                    break
                            if connecting:
                                break
            elif event.button == 3:  # Right click - Add switch
                new_switch = Switch(pos[0], pos[1], next_switch_id)
                switches.append(new_switch)
                next_switch_id += 1
            elif event.button == 2:  # Middle click - Add station
                new_station = Station(pos[0], pos[1], next_station_id)
                stations.append(new_station)
                next_station_id += 1
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if connecting:
                    pos = event.pos
                    for obj in switches + stations:
                        if obj != start_obj:
                            point_types = ["input", "straight", "diverging"] if isinstance(obj, Switch) else ["left", "right"]
                            for point_type in point_types:
                                if obj.is_over_point(pos, point_type):
                                    connections.append(Connection(start_obj, start_point, obj, point_type, temp_points))
                                    break
                            if connections and connections[-1].obj2 == obj:
                                break
                    connecting = False
                    start_obj = None
                    start_point = None
                    temp_points = []
                dragging = False
                selected_obj = None
        elif event.type == pygame.MOUSEMOTION and dragging:
            selected_obj.x = event.pos[0]
            selected_obj.y = event.pos[1]
            if isinstance(selected_obj, Switch):
                selected_obj.rect = pygame.Rect(event.pos[0] - SWITCH_WIDTH // 2, event.pos[1] - SWITCH_HEIGHT // 2, SWITCH_WIDTH, SWITCH_HEIGHT)
                selected_obj.input_point = (event.pos[0] - SWITCH_WIDTH // 2, event.pos[1])
                selected_obj.straight_point = (event.pos[0] + SWITCH_WIDTH // 2, event.pos[1])
                selected_obj.diverging_point = (event.pos[0] + SWITCH_WIDTH // 2 + DIVERGING_OFFSET_X, event.pos[1] + DIVERGING_OFFSET_Y)
            else:
                selected_obj.update_rect_and_points()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:  # Save
                encoded_layout = save_layout()
                print("Layout saved (base64):", encoded_layout)
            elif event.key == pygame.K_d and selected_obj:  # Delete
                # Remove connections involving the selected object
                connections[:] = [c for c in connections if c.obj1 != selected_obj and c.obj2 != selected_obj]
                if isinstance(selected_obj, Switch):
                    switches.remove(selected_obj)
                else:
                    stations.remove(selected_obj)
                selected_obj = None
            elif event.key == pygame.K_r and selected_obj and isinstance(selected_obj, Station):  # Rotate station
                selected_obj.rotation = 90 if selected_obj.rotation == 0 else 0
                selected_obj.update_rect_and_points()

    # Draw
    screen.fill(WHITE)
    for connection in connections:
        connection.draw(screen)
    for switch in switches:
        switch.draw(screen)
    for station in stations:
        station.draw(screen)
    if connecting:
        pos = pygame.mouse.get_pos()
        start_pos = {
            "input": start_obj.input_point if isinstance(start_obj, Switch) else start_obj.left_point,
            "straight": getattr(start_obj, "straight_point", None),
            "diverging": getattr(start_obj, "diverging_point", None),
            "left": start_obj.left_point if isinstance(start_obj, Station) else None,
            "right": start_obj.right_point if isinstance(start_obj, Station) else None
        }[start_point]
        if start_pos:
            points = [start_pos] + temp_points + [pos]
            pygame.draw.lines(screen, BLACK, False, points, 2)
    
    instructions = font.render("Right-click: Add switch | Middle-click: Add station | Left-click: Drag/Connect/Add point | D: Delete | R: Rotate station | S: Save", True, BLACK)
    screen.blit(instructions, (10, HEIGHT - 30))
    
    pygame.display.flip()

async def main():
    setup()
    while running:
        await update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())