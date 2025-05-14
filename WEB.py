import flask

app=flask.Flask(__name__)

import public_navigation.final as pn







if __name__=="__main__":
    app.run(port=9998, host="0.0.0.0")
 