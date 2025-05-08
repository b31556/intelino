import json
import random
import time
import flask
import requests

app=flask.Flask(__name__)

with open("map.json","r") as f:
    MAP=json.loads(f.read())

@app.route("/")
def index():
    return "Hello, World!"