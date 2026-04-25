import os
import threading
from urllib.error import URLError

import flask
import random
import selenium
import time
import requests
import io
import remotezip
import json
import re

from flask import url_for, send_file
from pip._internal.utils import datetime
from remotezip import RemoteZip
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib3.exceptions import ResponseError

GOOGLE_PHOTOS_ALBUM_LINK = ""
ZIP_FILE_LINK = ""
remote_images = []
remote_zip: RemoteZip
is_zip_file_refresher_running = False

def album_link_splitter(album_link):
    split_link = re.findall("[a-zA-Z0-9-_]+", album_link)
    return split_link[split_link.index("share")+1], split_link[split_link.index("key")+1]

def zip_file_refresher():
    """this is a long-running function"""
    global ZIP_FILE_LINK, GOOGLE_PHOTOS_ALBUM_LINK, remote_zip, remote_images, is_zip_file_refresher_running
    if is_zip_file_refresher_running: return
    is_zip_file_refresher_running = True
    try:
        album_id, album_key = album_link_splitter(GOOGLE_PHOTOS_ALBUM_LINK)
        link1 = f"https://photos.google.com/_/PhotosUi/data/batchexecute?rpcids=P3pCwd&source-path=%2Fshare%2F{album_id}"
        data1 = f"f.req=%5B%5B%5B%22P3pCwd%22%2C%22%5B%5B%5C%22{album_id}%5C%22%5D%2C%5C%22{album_key}%5C%22%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&"
        request1 = requests.post(link1, data1, headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
        returned_id = re.findall(r'(?<=\[\["wrb\.fr","P3pCwd","\[\\")[0-9a-f-]+', request1.text)
        if returned_id:
            returned_id = returned_id[0]
        else:
            raise URLError(f"here's the link I tried to fetch: {link1}\nhere's the data i tried to send: {data1}\nhere's the response: {request1.content()}")

        start_ts = time.time()
        response2_text = ""
        while time.time() - start_ts < 15 * 60 and response2_text.find("https://storage.googleapis.com/photos-web-downloads-anonymous/") == -1:
            time.sleep(5)
            link2 = f"https://photos.google.com/_/PhotosUi/data/batchexecute?rpcids=dnv2s&source-path=%2Fshare%2F{album_id}"
            data2 = f"f.req=%5B%5B%5B%22dnv2s%22%2C%22%5B%5B%5C%22{returned_id}%5C%22%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&"
            request2 = requests.post(link2, data2, headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
            response2_text = request2.text
            print(response2_text)

        if response2_text.find("https://storage.googleapis.com/photos-web-downloads-anonymous/") == -1:
            raise ResponseError(f"uh google sent stuff that seemed like it was fine but they never actually sent me the link to the zip file, what?\nhere's the id i got{returned_id}\nand here's the previous response: {response2_text}")
        else:
            with open("config.json", "r") as the_file:
                the_config = json.load(the_file)
                ZIP_FILE_LINK = re.findall(r'https:\/\/storage\.googleapis\.com\/photos-web-downloads-anonymous\/[0-9a-zA-Z-.\/]+', response2_text)[0]
                the_config["zip_file_link"] = ZIP_FILE_LINK
            with open("config.json", "w") as the_file2:
                json.dump(the_config, the_file2, indent=4)

        remote_images =[]
        remote_zip = RemoteZip(ZIP_FILE_LINK)
        raw_remote_images = remote_zip.filelist
        for image in raw_remote_images:
            if image.filename[-3:] in ("jpg", "png"):
                remote_images.append(image.filename)
        print(remote_images)
    except Exception as e:
        print(f"oh no oh dear something went wrong in the zip file refresher, here's the error: {e}")
    finally:
        is_zip_file_refresher_running = False


readonly_fs = False
try:
    os.listdir("assets/fetched")
except FileNotFoundError:
    try:
        os.mkdir("assets/fetched")
    except OSError:
        readonly_fs = True
        # I had considered doing some nice graceful handling to get it to run on vercel but i'm not using vercel anymore so it doesn't matter so i'm just raising an error
        raise FileNotFoundError("""AAAAAA i can't create files!! please run me on a file system that isn't read only (ie. not vercel)""")

no_config_file = False
try:
    f = open("config.json", "r")
    json.load(f)
    f.close()
except:
        open("config.json", "w").write(
            """
{
    "google_photos_album_link": "",
    "passkey": ""
}
            """)
        print("Fill in the config.json file! You only need to add the google photos album link and passkey (which is used to go at the end of the /getthelatestzipfileplease url because it's a long process and i wouldn't want people wasting your resources), i'll figure out some more stuff myself and add it later")
        exit()

with open("config.json", "r") as the_file:
    the_config = json.load(the_file)
    GOOGLE_PHOTOS_ALBUM_LINK = the_config["google_photos_album_link"]
    ZIP_FILE_LINK = the_config["zip_file_link"]
    #PASSKEY = the_config["passkey"]


app = flask.Flask(__name__, static_folder="assets")
#driver = webdriver.Chrome()
remote_images = []
try:
    remote_zip = RemoteZip(ZIP_FILE_LINK)
    raw_remote_images = remote_zip.filelist
    for image in raw_remote_images:
        if image.filename[-3:] in ("jpg", "png"):
            remote_images.append(image.filename)
    print(remote_images)
except remotezip.RemoteIOError:
    threading.Thread(target=zip_file_refresher).start()



@app.route("/random_image")
def get_image():
    #new_image_list = local_images
    #image_list = os.listdir("assets")
    #new_image_list = []
    #for image in image_list:
    #    new_image_list.append(f"./assets/{image}")
    try:
        local_images = os.listdir("assets/fetched")
        big_image_list = local_images + remote_images
        image = random.choice(big_image_list)
        if not readonly_fs:
            if image[image.find("/")+1:] not in local_images:
                try:
                    remote_zip.extract(image, f"./assets/fetched")
                    os.rename(f"./assets/fetched/{image}", f"./assets/fetched/{image[image.find("/")+1:]}")
                except:
                    image = random.choice(local_images)
                    threading.Thread(target=zip_file_refresher).start()
            return send_file(f"./assets/fetched/{image[image.find("/")+1:]}", mimetype="image")
        else:
            try:
                image_data = remote_zip.read(image)
                return send_file(io.BytesIO(image_data), mimetype="image")
            except:
                threading.Thread(target=zip_file_refresher).start()
                return send_file(image, mimetype="image")
    except:
        threading.Thread(target=zip_file_refresher).start()
        return send_file("./assets/fallback.png", "image")

    #return #send_file(io.BytesIO(requests.get(random.choice(local_images)).content), mimetype="image") # send_file(random.choice(new_image_list), mimetype="image")

@app.route("/")
def index():
    return flask.render_template("index.html")

"""
def do_selenium_getting(): # Might not use because vercel can't use selenium
    counter = 0
    driver.get(GOOGLE_PHOTOS_ALBUM_LINK)
    time.sleep(random.random()*2.13 + 0.92) # Hopefully convince google it's not a bot?
    driver.find_element(By.CLASS_NAME, "p137Zd").click() # Clickable image card
    time.sleep(random.random()*1.4 + 1.2)
    while "RDPZE" not in driver.find_element(By.CLASS_NAME, "Cwtbxf").get_attribute("class") and counter < 10: # RDPZE is the class that gets added to Cwtbxf, the right arrow, when the end of the list has been reached
        time.sleep(random.random()*0.53 + 0.21)
        img = driver.find_element(By.CLASS_NAME, "BiCYpc").get_attribute("src") # BiCYpc is the image when big
        print(img) # Image but big
        local_images.append(str(img))
        ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
        counter += 1
"""

#zip_file_refresher()

app.run()

# regex for image links with w h at the end https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+=w[0-9]+-h[0-9]+
# regex for all image links https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9-_]+
# rainbow red, orange, yellow, lawngreen, dodgerblue, blueviolet, red, orange, yellow, lawngreen, dodgerblue, blueviolet, red, orange, yellow, lawngreen, dodgerblue, blueviolet