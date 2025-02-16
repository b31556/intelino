
# webserver

import flask
from flask import request, jsonify, send_file
import os
import json
import io

app=flask.Flask("train_web")

colorMAP={}

want= False # do you want drwed map or networkx graph

if "track.png" in os.listdir() and "colors.txt" in os.listdir() and want:
    mode=True
    print("track.png exists")
    import track_draw as td
    with open("colors.txt") as f:
        colors = f.readlines()
        for co in colors:
            track,color=co.split(":")
            track=int(track.strip())
            color=json.loads(color.strip().replace("(","[").replace(")","]"))
            colorMAP[track]=color
    print(colorMAP)
else:
    import track_visulizer as td


@app.route("/")
def index():
    img=td.prepare_map({(0,255,112):3},colorMAP)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def run(port=8585):
    app.run(host='127.0.0.1', port=port)
  

if __name__ == '__main__':
    run()



