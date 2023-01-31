from http import server
from flask import Flask, Response, send_from_directory, request, redirect, jsonify, flash, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageColor
import os, sys, json, atexit, math, random, logging

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

among_bod = {
    "points": [(1,0), (2,0), (3,0), (0,1), (1,1), (0,2), (1,2), (2,2), (3,2), (1,3), (2,3), (3,3), (1,4), (3,4)],
    "size": { "x": 4, "y": 5 },
    "face": [(2,1), (3,1)],
    "face_colour_change": {"r": 24, "g": 15, "b": 15, "a": 0},
    "modulus": 8,
    "y_offset": 4,
    "y_space": 2
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


# COLOUR FUNCTIONS

def invert_colour(colour):
    amount = server_status["filter_settings"]["invert-amount"]
    #print(amount)
    if (amount != 0):
        if (amount == ""):
            amount = 100
        print(amount)
        amount = 100 / amount
        #print("before " + r + " " + g + ' ' + b)
        r = int( (255 - colour[0]) / amount)
        g = int( (255 - colour[1]) / amount)
        b = int( (255 - colour[2]) / amount)
        a = colour[3]
        #print("before " + r + " " + g + ' ' + b)
    else:
        r = colour[0]
        g = colour[1]
        b = colour[2]
        a = colour[3]
    return (r, g, b, a)

def average_colours(colour_list):
    colours = 0
    r = 0
    g = 0
    b = 0
    a = 0
    for col in colour_list:
        colours += 1
        r += col[0]
        g += col[1]
        b += col[2]
        a += col[3]
    return (r / colours, g / colours, b / colours, a / colours)

def fancy_round(number):
    out = 0
    if ( number - math.floor(number ) >= 0.5): #if just decimal place is greater than or equal to 0.5
        out = math.ceil(number) #round up
    elif ( number - math.floor(number ) < 0.5): #if just decimal place is less than 0.5
        out = math.floor(number) #round down
    return out


@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    global server_status

    server_status["processing_complete"] = False
    server_status["primary_uploads"] = []
    print(bc.WARNING + bc.BOLD + "clearing photos...\n" + bc.END)
    clear_photos()
    
    if request.method == 'POST':

        server_status["filter_settings"]["invert-amount"] = int(request.form.get("invert-amount"))
        if (int(request.form.get("scale")) != 0):
            server_status["filter_settings"]["scale"] = int(request.form.get("scale"))
        else:
            server_status["filter_settings"]["scale"] = 0
        if (request.form.get("overlay") == None):
            server_status["overlay"] = False
        else:
            server_status["overlay"] = True

        #server_status["overlay"]

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
        og_img = img_tm.convert("RGBA")
        img_width, img_height = img_tm.size
        img_out = img_tm
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
                for y in range(0, img_height):
                    # for y ways
                    for x in range(0, img_width):
                        # for x ways
                        og_colour  = data[y][x]
                        img_tm.putpixel((x,y), (invert_colour(og_colour)))
                img_out = img_tm
            case "among us dither":
                dither_scale = server_status["filter_settings"]["scale"]

                if (dither_scale == 0):
                    # scale is auto
                    dither_scale = 1 # for now set it to 1 but when im able to i need to make it auto-scale
                
                dither_scale = math.floor(dither_scale)
                
                print("dither scale: " + str(dither_scale))

                img_tm = img_tm.resize((math.floor(img_width / dither_scale), math.floor(img_height / dither_scale)))
                og_img = og_img.resize((math.floor(img_width / dither_scale), math.floor(img_height / dither_scale)))
                img_width, img_height = img_tm.size

                col_img_width = math.ceil(img_width)
                col_img_height = math.ceil(img_height / 2)

                tm = Image.new("RGBA", (col_img_width, col_img_height * 2), (000, 000, 000, 000)) # new image to draw on
                res = ( math.ceil(img_width / ( among_bod["size"]["x"] )), math.ceil(img_height / ( ( among_bod["size"]["y"] + among_bod["y_space"]) )) )
                img_tm = img_tm.resize(res)
                #img_tm.show()
                small_img_width, small_img_height = img_tm.size

                #img_tm.show()
                #print(str(small_img_width) + ", " + str(small_img_height) )

                tm_draw = ImageDraw.Draw(tm)

                def draw_amogus(x, y, colour):

                    # generate helmet colour
                    colour_r = colour[0]
                    colour_g = colour[1]
                    colour_b = colour[2]
                    colour_a = colour[3]
                    col_face_r = colour_r + among_bod["face_colour_change"]["r"]    # apply colour change
                    col_face_g = colour_g + among_bod["face_colour_change"]["g"]
                    col_face_b = colour_b + among_bod["face_colour_change"]["b"]
                    col_face_a = colour_a + among_bod["face_colour_change"]["a"]
                    if (col_face_r > 255):                                          # if its greater than 255, subtract instead
                        col_face_r = colour_r - among_bod["face_colour_change"]["r"]
                    if (col_face_g > 255):
                        col_face_g = colour_g - among_bod["face_colour_change"]["g"]
                    if (col_face_b > 255):
                        col_face_b = colour_b - among_bod["face_colour_change"]["b"]
                    if (col_face_a > 255):
                        col_face_a = colour_a - among_bod["face_colour_change"]["a"]

                    def draw_point_list(list_tm, tm_colour):
                        for cords in list_tm:
                            x_coord_base = x + cords[0]  # base colour x coord * among us width (treating 1 amogus as a pixel) + whatever the bod coord is
                            x_coord_end = x + cords[0]
                            y_coord_base = y + cords[1]   # base colour y coord * among us width (treating 1 amogus as a pixel) + whatever the bod coord is
                            y_coord_end = y + cords[1]
                            
                            #print("draw [" + str(x_coord_base) + ", " + str(y_coord_base) + "] to [" + str(x_coord_end) + ", " +  str(y_coord_end) + "] with colour (" + str(colour_tm[0]) + " " + str(colour_tm[1]) + " " + str(colour_tm[2]) + " " + str(colour_tm[3]) + ")" )
                            
                            tm_draw.rectangle( xy=[x_coord_base, y_coord_base, x_coord_end, y_coord_end], fill=(tm_colour[0], tm_colour[1], tm_colour[2], tm_colour[3]))
                    status_message("drawing amogi bodies...")
                    draw_point_list(among_bod["points"], [colour_r, colour_g, colour_b, colour_a])
                    status_message("drawing amogi helmets...")
                    draw_point_list(among_bod["face"], [col_face_r, col_face_g, col_face_b, col_face_a])
                    
                    

                for y in range(-1 * small_img_height, small_img_height):
                    # for y ways
                    for x in range(0, small_img_width):
                        # for x ways
                        def get_y_offset(y_val, x):
                            #print(y_val)
                            #print(small_img_height)

                            odd_even = (x + 1) % 2

                            
                            def calc_amogi(am):
                                return (am * among_bod["size"]["y"]) + (am * among_bod["y_space"] )

                            y_val = ( calc_amogi(y_val) + ( x / 2) )

                            if (odd_even == 0):
                                y_val += among_bod["y_offset"]
                            else:
                                y_val += 0
                            
                            #section_number = math.floor(x/17)

                            #y_val -= calc_amogi(section_number + 1)

                            return y_val

                        y_tm = get_y_offset(y, x)

                        x = x * among_bod["size"]["x"]
                        #y = y * among_bod["size"]["y"]

                        #if (y_tm >= img_height):
                            #rint(y)
                            #y_tm = y_tm - ( ( (img_height - 1) - math.ceil( (img_width - 1) / 2) ) * 2 )


                        colour_y = y_tm / ( among_bod["size"]["x"] + 3)

                        if (colour_y >= small_img_height):
                            colour_y = 0
                            #y = (small_img_height - y)
                        if (colour_y < 0):
                            colour_y = 0
                        
                        colour_tm = img_tm.getpixel((x / among_bod["size"]["x"], colour_y))
                        draw_amogus(x, y_tm, colour_tm) #draw the amogus

                
                if (server_status["overlay"] == True):
                    img_out = og_img
                    #og_img.show()
                    img_out.paste(tm, (0,0), mask=tm)
                else:
                    img_out = tm


        out_filename = str(im_filename.split(".")[0]) + ".png"

        img_out.save(os.path.join(PROCESSED_FOLDER, out_filename))



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




