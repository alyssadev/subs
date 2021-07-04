#!/usr/bin/env python3

from flask import *
from glob import glob
from string import ascii_lowercase, ascii_uppercase, digits
import os.path
from json import load, loads
from io import BytesIO
from math import floor

app = Flask(__name__)

def s2ts(inp):
    # seconds to timestamps: converts e.g 0 to 00:00:00,000, 2.427 to 00:00:02,427
    if inp < 0:
        inp = 0
    s,ms = divmod(inp,1)
    m,s = divmod(s,60)
    h,m = divmod(m,60)
    return f"{h:02.0f}:{m:02.0f}:{s:02.0f},{floor(ms*100):02.0f}"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                  '63546997.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/<channel>/<video_id>.srt")
def srt(channel, video_id):
    if channel[:2] != "UC" or any(c not in ascii_lowercase + ascii_uppercase + digits + "_" for c in channel) or len(channel) != 24:
        return "", 404
    if any(c not in ascii_lowercase + ascii_uppercase + digits + "_-" for c in video_id) or len(video_id) != 11:
        return "", 404
    try:
        with open(os.path.join("cache", channel, video_id + ".json")) as f:
            data = load(f)
    except:
        return "", 404
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
    return send_file(BytesIO("\n".join(out).encode("utf-8")), mimetype="text/plain", attachment_filename=video_id + ".srt", as_attachment=True)

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
