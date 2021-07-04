#!/usr/bin/env python3

from flask import *
from glob import glob
from string import ascii_lowercase, ascii_uppercase, digits
import os.path
from json import load

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                  '63546997.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/<channel>/")
def view(channel):
    if channel[:2] != "UC" or any(c not in ascii_lowercase + ascii_uppercase + digits + "_" for c in channel) or len(channel) != 24:
        return "", 404
    try:
        with open(os.path.join("cache", channel, "ids")) as f:
            ids = [_.strip() for _ in f]
    except:
        return "Channel not configured", 404
    data = {"_has": [], "_doesnt": []}
    yt_data = {}
    for i in ids:
        with open(os.path.join("cache", channel, i + ".json")) as f:
            vid = load(f)
        data[i] = vid
        with open(os.path.join("cache", channel, i + ".yt")) as f:
            yt = load(f)
        yt_data[i] = yt
        if vid["subtitles"]["Items"]:
            data["_has"].append(i)
        else:
            data["_doesnt"].append(i)
    return render_template("channel.html", data=data, yt_data=yt_data)

@app.route("/<channel>")
def redir(channel):
    if channel[:2] != "UC" or any(c not in ascii_lowercase + ascii_uppercase + digits + "_" for c in channel) or len(channel) != 24:
        return "", 404
    return redirect("/{}/".format(channel))

@app.route("/")
def index():
    from glob import glob
    channels = {}
    for c in glob(os.path.join("cache", "*")):
        i = glob(os.path.join(c, "*.json"))[0]
        with open(i) as f:
            d = load(f)
            channels[c[6:]] = d["video-details"]["channelTitle"]
    return render_template("index.html", channels=channels)

if __name__ == "__main__":
    app.run(port=48000)
