import os
import json
import time
import requests
import argparse
import datetime
import mta_utils as utils

from tqdm import tqdm
from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError

now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# http://mtadatamine.s3-website-us-east-1.amazonaws.com/#/subwayRealTimeFeeds
default_feed_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
default_sleep_sec = 2

parser = argparse.ArgumentParser()
parser.add_argument("--feed", default=default_feed_url)
parser.add_argument("--api_key")
parser.add_argument("--output", default=f"./mta-subway-{now}.log")
parser.add_argument("--runtime", type=int, default=60)
args = parser.parse_args()

print(f"Writing MTA subway data to file: {args.output}")
print(f"Collecting data for {args.runtime} minutes")

api_key = args.api_key
if not api_key:
    api_key = os.getenv("MTA_API_KEY")
if args.feed and not api_key:
    parser.error("--api_key must be specified with --feed")

runtime_mins = args.runtime
if runtime_mins < 1:
    runtime_mins = 1

with open(args.output, "w") as out:
    for i in tqdm(range(int(runtime_mins*60/default_sleep_sec))):
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(
            args.feed,
            headers={"x-api-key": api_key}
        )
        try:
            feed.ParseFromString(response.content)
        except DecodeError:
            print(f"Decode error: {response.content}")
            break
        for entity in feed.entity:
            message = utils.parse_entity(entity)
            if message:
                out.write(json.dumps(message) + "\n")
        time.sleep(2)
