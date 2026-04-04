import os
import flask
import random

from flask import url_for, send_file

app = flask.Flask(__name__, static_folder="assets")

@app.route("/random_image")
def get_image():
    image_list = os.listdir("assets")
    new_image_list = []
    for image in image_list:
        new_image_list.append(f"./assets/{image}")
    return send_file(random.choice(new_image_list), mimetype="image")

@app.route("/")
def index():
    return flask.render_template("index.html")


app.run()