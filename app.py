import os
import flask
import random
import selenium
import time
import requests
import io

from flask import url_for, send_file
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# TODO: add a cache of images
app = flask.Flask(__name__, static_folder="assets")
driver = webdriver.Chrome()
images = []

@app.route("/random_image")
def get_image():
    #new_image_list = images
    #image_list = os.listdir("assets")
    #new_image_list = []
    #for image in image_list:
    #    new_image_list.append(f"./assets/{image}")
    print(images)
    print(random.choice(images))
    return send_file(io.BytesIO(requests.get(random.choice(images)).content), mimetype="image") # send_file(random.choice(new_image_list), mimetype="image")

@app.route("/")
def index():
    return flask.render_template("index.html")

counter = 0
driver.get("https://photos.google.com/share/AF1QipOhkv3JKQkgQvaKeVyOhHpj5izKMlu2UExQMP6rw0Y0EmXRwIjK9qhGKKYDDD2iDA?key=dFFSU1h6MEt3YVNDeHNCUUdSamhwRXoxckR0LVNB")
time.sleep(random.random()*2.13 + 0.92) # Hopefully convince google it's not a bot?
driver.find_element(By.CLASS_NAME, "p137Zd").click() # Clickable image card
time.sleep(random.random()*1.4 + 1.2)
while "RDPZE" not in driver.find_element(By.CLASS_NAME, "Cwtbxf").get_attribute("class") and counter < 10: # RDPZE is the class that gets added to Cwtbxf, the right arrow, when the end of the list has been reached
    time.sleep(random.random()*0.53 + 0.21)
    img = driver.find_element(By.CLASS_NAME, "BiCYpc").get_attribute("src") # BiCYpc is the image when big
    print(img) # Image but big
    images.append(str(img))
    ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
    counter += 1


#app.run()

# regex for image links with w h at the end https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+=w[0-9]+-h[0-9]+
# regex for all image links https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+
# rainbow red, orange, yellow, lawngreen, dodgerblue, blueviolet, red, orange, yellow, lawngreen, dodgerblue, blueviolet, red, orange, yellow, lawngreen, dodgerblue, blueviolet