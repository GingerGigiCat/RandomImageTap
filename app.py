import os
import flask
import random
import requests

from flask import url_for, send_file
# TODO: add google photos album integration?
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

print(requests.get("https://photos.google.com/share/AF1QipOhkv3JKQkgQvaKeVyOhHpj5izKMlu2UExQMP6rw0Y0EmXRwIjK9qhGKKYDDD2iDA?key=dFFSU1h6MEt3YVNDeHNCUUdSamhwRXoxckR0LVNB").content)
#app.run()

# regex for image links with w h at the end https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+=w[0-9]+-h[0-9]+
# regex for all image links https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+