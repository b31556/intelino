import json
import random
import time
import flask
import requests

#app=flask.Flask(__name__)

with open("real/map.json","r") as f:
    MAP=json.loads(f.read())

timetable= ["st1","st3","st1","st4"]

istrainstarted=False

while True:
    time.sleep(0.2)

    try:
        position=requests.get("http://127.0.0.1:5080/get_positions").json()
        if position=={}:
            if not istrainstarted:
                print("Train started")
                istrainstarted=True
                dest=timetable.pop(0)
                print("Destination: ",dest)
                requests.post("http://127.0.0.1:5080/set_plan/0",data=dest)

                continue

        positions=position[list(position.keys())[0]]
        destination=requests.get("http://127.0.0.1:5080/get_destinations").json()
        if destination=={}:
            print("Train started")
            istrainstarted=True
            dest=timetable.pop(0)
            print("Destination: ",dest)
            requests.post("http://127.0.0.1:5080/set_plan/0",data=dest)

            continue

        destination=destination[list(destination.keys())[0]]

        if positions==destination:
            print(f"arrived at {position}")
            time.sleep(5)

            dest=timetable.pop(0)
            print(f"new destination {dest}")
            requests.post(f"http://127.0.0.1:5080/set_plan/0",data=dest)

            continue

    except requests.exceptions.ConnectionError:
        print("Server not running")
        time.sleep(5)
        print("Trying again")
    except KeyboardInterrupt:
        print("Stopping")
        break
    


