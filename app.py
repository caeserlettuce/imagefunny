from http import server
from flask import Flask, Response, send_from_directory, request, redirect, jsonify, flash, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageColor
import os, sys
import json
import atexit
import math
import random
import logging
now = datetime.now()
log_file = "log.json"

class bc:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


UPLOAD_FOLDER = "./uploads"
PROCESSED_FOLDER = "./processed"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG', "PNG"}
CLEAR_PHOTOS_ON_SHUTDOWN = True #set this to false if you want it to keep photos when you shut down the server
server_status = {
    "message": "",
    "primary_uploads": [],
    "secondary_uploads": [],
    "filters": {},
    "settings": ["base_image", "secondary_image"],  # list of ids for the form settings
    "selected_image": "",
    "selected_secondary_image": "",
    "processing_complete": False,
    "current_filter": "",
    "filter_settings": {}
}


filters_file = open("filters.json", "r")
try:
    filters_json = json.load(filters_file)
except:
    filters_json = {
        "filters": {
            "nothing": {
                "title": "nothing",
                "description": "nothing",
                "parameters": ["base image"]
            },
            "greyscale": {
                "title": "greyscale",
                "description": "turns the image greyscale",
                "parameters": ["base image"]
            }
        }
    }
    print(bc.FAIL + bc.BOLD + bc.UNDERLINE + "filters.json is broken! using emergency filters!" + bc.END)
filters_file.close()
server_status["filters"] = filters_json["filters"]


def clear_photos():
    for filename in os.listdir(UPLOAD_FOLDER):
        print(bc.WARNING + "removing image \"" + filename + "\"" + bc.END)
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
    for filename in os.listdir(PROCESSED_FOLDER):
        print(bc.WARNING + "removing image \"" + filename + "\"" + bc.END)
        os.remove(os.path.join(PROCESSED_FOLDER, filename))

def exit_handler():
    print(bc.FAIL + bc.BOLD + "\nclosing..." + bc.END)
    if (CLEAR_PHOTOS_ON_SHUTDOWN == True):
        print(bc.WARNING + "\"clear photos on shutdown\" is set to true!\n" + bc.END)
        clear_photos()


print(bc.HEADER + "to host on the local network, run 'flask run --host=0.0.0.0'" + bc.END)

atexit.register(exit_handler)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))

def get_file(filename):
    try:
        src = os.path.join(root_dir(), filename)
        return open(src).read()
    except IOError as exc:
        return str(exc)


@app.route('/<path:path>')
def send_report(path):
    return send_from_directory('.', path)


@app.route("/", methods=['GET', 'POST'])
def route_home():


    return Response(get_file('home.html'))

def done_processing():
    server_status["processing_complete"] = True

def status_message(message):
    server_status["message"] = message

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    global server_status

    server_status["processing_complete"] = False
    server_status["primary_uploads"] = []
    print(bc.WARNING + bc.BOLD + "clearing photos...\n" + bc.END)
    clear_photos()
    
    if request.method == 'POST':

        server_status["filter_settings"]["invert-amount"] = request.form.get("invert-amount")

        uploaded_files_1 = request.files.getlist("file1")
        for f in uploaded_files_1:
            print(f)
            if (f.filename != ""):
                server_status["primary_uploads"].append(f.filename)
                server_status["selected_image"] = f.filename.replace(" ", "_")
                f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
                status_message("processing...")


        uploaded_files_2 = request.files.getlist("file2")
        for f in uploaded_files_2:
            print(f)
            if (f.filename != ""):
                server_status["secondary_uploads"].append(f.filename)
                server_status["selected_secondary_image"] = f.filename.replace(" ", "_")
                f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
                status_message("processing...")
            
        # do the image thing

        filter = server_status["current_filter"]
        im_filename = server_status["selected_image"]


        img_tm = Image.open(os.path.join(UPLOAD_FOLDER, im_filename)) # open image
        img_tm = img_tm.convert("RGBA")
        img_width, img_height = img_tm.size
        data = []
        for y in range(0, img_height):
            # for y ways
            data.append([])
            for x in range(0, img_width):
                # for x ways
                data[y].append(img_tm.getpixel((x, y)))

        # use this to set pixels
        #img_tm.putpixel((x,y), (r, g, b))
        
        
        match filter:
            case "nothing":
                print("why are you doing nothing")
                img_out = img_tm
            case "greyscale":
                img_out = ImageOps.grayscale(img_tm)
            case "invert":
                print("inverting")                


        img_out.save(os.path.join(PROCESSED_FOLDER, im_filename))



        done_processing()
        status_message("done processing!")
        return redirect("/")



@app.route('/status', methods=['GET'])
def get_server_message():
    #GET request
    if request.method == 'GET':
        return jsonify(server_status)



@app.route('/filter', methods=['POST'])
def set_filter():
    #POST request
    global server_status
    if (request.method == "POST"):
        server_status["current_filter"] = request.get_json()["filter"]
        print("selected filter: " + server_status["current_filter"])
        return "hee hee: a michael jackson story"




