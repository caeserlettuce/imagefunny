from flask import Flask, Response, send_from_directory, request, redirect, jsonify
from datetime import datetime
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

def write_log_file(json_tm):
    json_tm = str(json).replace("'", '"')
    log_db_file.write(json.dumps(log_db))

def parse_request(req):
    print(req.remote_addr)


def exit_handler():
    print("closing")
    write_log_file(log_db)
    log_db_file.close()


print(bc.HEADER + "to host on the local network, run 'flask run --host=0.0.0.0'" + bc.END)
log_db_file = open(log_file, "r")
try:
    log_db = json.load(log_db_file)
    heehee = log_db["entries"]
except:
    log_db = {"entries": []}

log_db_file.close()
log_db_file = open(log_file, "w")

print(log_db)

atexit.register(exit_handler)
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))

def get_file(filename):
    try:
        src = os.path.join(root_dir(), filename)
        return open(src).read()
    except IOError as exc:
        return str(exc)

@app.route('/assets/<path:path>')
def send_report(path):
    return send_from_directory('assets', path)

@app.route("/", methods=['GET', 'POST'])
def route_home():
    parse_request(request)
    return Response(get_file('home.html'))

# TODO
#
# [ x ] submit button for the card choosing
# [ x ] a consistent hand
# [ x ] display who won when name reveal happens