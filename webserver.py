
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
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Full Screen Image Refresh</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
        }
        #background-image {
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            z-index: -1; /* Keeps the image in the background */
        }
    </style>
</head>
<body>

<img id="background-image" src="http://127.0.0.1:8585/p" alt="Background Image">

<script>
    setInterval(function() {
        const img = document.getElementById('background-image');
        img.src = img.src.split('?')[0] + '?' + new Date().getTime(); // Add timestamp to avoid caching
    }, 500); // Refresh image every 5 seconds
</script>

</body>
</html>"""


@app.route("/p")
def index():
    img=td.draw_map()
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def run(port=8585):
    app.run(host='127.0.0.1', port=port)
  

if __name__ == '__main__':
    run()



