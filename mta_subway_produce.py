import os
import json
import requests
import argparse
import time
import datetime
import mta_utils as utils

from kafka import KafkaProducer
from mta_reference import MTAReference

from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError

# http://mtadatamine.s3-website-us-east-1.amazonaws.com/#/subwayRealTimeFeeds
default_feed_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"

parser = argparse.ArgumentParser()
parser.add_argument("--brokers", default="localhost:9092")
parser.add_argument("--topic", default="gtfs_mta_subway")
parser.add_argument("--feed", default=default_feed_url)
parser.add_argument("--api_key")
parser.add_argument("--ref_dir", default="ref")
parser.add_argument("--enrich", action="store_true")
parser.add_argument("--runtime", type=int, default=60)
args = parser.parse_args()

api_key = args.api_key
if not api_key:
    api_key = os.getenv("MTA_API_KEY")
if args.feed and not api_key:
    parser.error("--api_key must be specified with --feed")
print(f"Feed: {args.feed}")

runtime_mins = args.runtime
if runtime_mins < 1:
    runtime_mins = 1
end = datetime.datetime.now() + datetime.timedelta(minutes=runtime_mins)

base_dir = args.ref_dir
ref = MTAReference(base_dir)

utils.create_topic(args.brokers, args.topic)
producer = KafkaProducer(
    bootstrap_servers=args.brokers,
    compression_type="gzip"
)

def on_success(metadata):
    print(f"Sent to topic '{metadata.topic}' at offset {metadata.offset}")

def on_error(e):
    print(f"Error sending message: {e}")

while True:
    if datetime.datetime.now() >= end:
        break
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
        message = utils.parse_entity(entity, enrich=args.enrich, ref=ref)
        if message:
            future = producer.send(
                args.topic,
                key=str.encode(entity.id),
                value=json.dumps(message).encode()
            )
            future.add_callback(on_success)
            future.add_errback(on_error)
    time.sleep(2)

producer.flush()
producer.close()
