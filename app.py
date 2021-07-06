#!/usr/bin/env python3

from flask import *
from flask_cors import cross_origin
from glob import glob
from string import ascii_lowercase, ascii_uppercase, digits
import os.path
from json import load, loads
from io import BytesIO
from math import floor
from random import choice

app = Flask(__name__)
app.secret_key = "".join(choice(ascii_lowercase + ascii_uppercase + digits + "!@#$%^&**()_+-=[]{}") for _ in range(50))

validate_channel = lambda channel: channel[:2] == "UC" and all(c in ascii_lowercase + ascii_uppercase + digits + "_" for c in channel) and len(channel) == 24
validate_video_id = lambda video_id: all(c in ascii_lowercase + ascii_uppercase + digits + "_-" for c in video_id) and len(video_id) == 11

def s2ts(inp):
    # seconds to timestamps: converts e.g 0 to 00:00:00,000, 2.427 to 00:00:02,427
    if inp < 0:
        inp = 0
    s,ms = divmod(inp,1)
    m,s = divmod(s,60)
    h,m = divmod(m,60)
    return f"{h:02.0f}:{m:02.0f}:{s:02.0f},{floor(ms*100):02.0f}"

def video_data(channel, video_id):
    if not validate_channel(channel):
        return "Invalid channel ID", None, 404
    if not validate_video_id(video_id):
        return "Invalid video ID", None, 404
    try:
        with open(os.path.join("cache", channel, video_id + ".json")) as f:
            data = load(f)
        with open(os.path.join("cache", channel, video_id + ".yt")) as f:
            yt_data = load(f)
    except:
        return "Video ID not found", 404
    return data, yt_data, 200

def channel_data(channel):
    if not validate_channel(channel):
        return "Invalid channel ID", None, 404
    try:
        with open(os.path.join("cache", channel, "ids")) as f:
            ids = [_.strip() for _ in f]
    except:
        return "Channel not configured", None, 404
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
    return data, yt_data, 200

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                  '63546997.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/<channel>/<video_id>.srt")
@cross_origin()
def srt(channel, video_id):
    fn = video_id + ".srt"
    if len(video_id) > 11 and video_id[-12] == "-":
        # filename requested
        video_id = video_id[-11:]
    data, yt_data, retcode = video_data(channel, video_id)
    if retcode != 200:
        flash(data)
        return redirect(url_for("index"))
    if len(data["subtitles"]["Items"]) == 0:
        flash("Video has no subtitles yet")
        return redirect(url_for("index"))
    # I hate this very much
    sub = loads(loads(data["subtitles"]["Items"][0]["subtitles"]["S"]))
    fmt = "{n}\n{ts1} --> {ts2}\n{line}\n"
    out = []
    for n,l in enumerate(sub):
        ts1 = s2ts(l["start"])
        ts2 = s2ts(l["end"])
        out.append(fmt.format(n=n+1, ts1=ts1, ts2=ts2, line=l["text"]))
    return send_file(BytesIO("\n".join(out).encode("utf-8")), mimetype="text/plain", attachment_filename=fn, as_attachment=True)

@app.route("/<channel>/")
def channel_view(channel):
    data, yt_data, retcode = channel_data(channel)
    if retcode != 200:
        flash(data)
        return redirect(url_for("index"))
    return render_template("channel.html", data=data, yt_data=yt_data)

@app.route("/<channel>/.json")
@cross_origin()
def channel_json(channel):
    data, yt_data, retcode = channel_data(channel)
    if retcode != 200:
        return jsonify({"error": data, "code": retcode})
    return jsonify({"data": data, "yt_data": yt_data})

@app.route("/<channel>/<video_id>.json")
@cross_origin()
def video_json(channel, video_id):
    data, yt_data, retcode = video_data(channel, video_id)
    if retcode != 200:
        return jsonify({"error": data, "code": retcode})
    return jsonify({"data": data, "yt_data": yt_data})

def channel_list():
    from glob import glob
    channels = {}
    for c in glob(os.path.join("cache", "*")):
        i = glob(os.path.join(c, "*.json"))[0]
        with open(i) as f:
            d = load(f)
            channels[c[6:]] = d["video-details"]["channelTitle"]
    return channels

@app.route("/.json")
@cross_origin()
def index_json():
    channels = channel_list()
    return jsonify({"channels": channels})

@app.route("/")
def index():
    channels = channel_list()
    return render_template("index.html", channels=channels)

if __name__ == "__main__":
    app.run(port=48000)
