from intelino.trainlib import TrainScanner, Train
from intelino.trainlib.enums import (
    SnapColorValue as C,
    MovementDirection
)

def station_detected(train, msg):
    print(f"Train {train.id} detected a station with colors: {msg.colors}")  

    if msg.colors[:3] == (C.WHITE, C.MAGENTA, C.GREEN):   # if it is the right station
        train.stop_driving()   # we stop the train
        print(f"Train {train.id} stopped at the station.")
        
def main():
    # Initialize the train scanner and scan for trains
    NUMBER_OF_TRAINS = 1
    scanner = TrainScanner()
    trains = scanner.get_trains(NUMBER_OF_TRAINS)

    for train in trains:
        # start the train at speed 40 forward
        train.drive_at_speed(40, MovementDirection.FORWARD)

        # Add a listener for snap command detection
        # This is a callback function that will be called when a snap command is detected
        train.add_snap_command_detection_listener(station_detected)

        # Print the train's ID
        print(f"Train ID: {train.id}")

    # Keep the script running to listen for events
    input("Press Enter to exit...")
    for train in trains:
        train.stop_driving()  # Stop the train when exiting
        print(f"Train {train.id} stopped.")

if __name__ == "__main__":
    main()
