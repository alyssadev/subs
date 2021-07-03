#!/usr/bin/env python3
from requests import get, post
from json import dump, load
from sys import argv
from os import environ, makedirs
import os.path

key = environ.get("YOUTUBE_KEY")

def get_vids(channel_id, cache=True):
    try:
        if cache:
            with open(os.path.join("cache", channel_id, "ids")) as f:
                for line in f:
                    yield line.strip()
        else:
            raise Exception
    except:
        ids = []
        playlist_id = "UU" + channel_id[2:]
        api_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {"part": "snippet", "maxResults": "50", "playlistId": playlist_id, "key": key}
        while True:
            vids = get(api_url, params=params).json()
            for vid in vids["items"]:
                ids.append(vid["snippet"]["resourceId"]["videoId"])
                yield vid["snippet"]["resourceId"]["videoId"]
            if "nextPageToken" in vids:
                params["pageToken"] = vids["nextPageToken"]
            else:
                break
        with open(os.path.join("cache", channel_id, "ids"), "w") as f:
            f.write("\n".join(ids))

def get_subs_data(video_id, cache=True, channel_id=None):
    try:
        if cache and channel_id:
            with open(os.path.join("cache", channel_id, video_id + ".json")) as f:
                return load(f)
        else:
            raise Exception
    except:
        data = post("https://vznx16favj.execute-api.us-east-1.amazonaws.com/default/getSubtitles?videoID=" + video_id).json()
        with open(os.path.join("cache", "UC" + data["video-details"]["channelId"][2:], video_id + ".json"), "w") as f:
            dump(data,f)
        return data

def get_yt_subs_data(video_id, channel_id, cache=True):
    try:
        if cache and channel_id:
            with open(os.path.join("cache", channel_id, video_id + ".yt")) as f:
                return load(f)
        else:
            raise Exception
    except:
        api_url = "https://www.googleapis.com/youtube/v3/captions"
        params = {"part": "snippet", "videoId": video_id, "key": key}
        data = get(api_url, params=params).json()
        with open(os.path.join("cache", channel_id, video_id + ".yt"), "w") as f:
            dump(data,f)
        return data

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("channel")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    try:
        os.makedirs(os.path.join("cache", args.channel))
    except FileExistsError:
        pass
    ids = [i for i in get_vids(args.channel, cache=not args.no_cache)]
    print("retrieved list of video ids: {} videos".format(len(ids)))
    for i in ids:
        _ = get_subs_data(i, cache=not args.no_cache, channel_id=args.channel)
        print("got {}: {} subs".format(i, _["subtitles"]["Count"]))
        _ = get_yt_subs_data(i, args.channel, cache=True)
        print("yt  {}: {} subs".format(i, len(_["items"])))
    return 0

if __name__ == "__main__":
    from sys import exit
    exit(main())
