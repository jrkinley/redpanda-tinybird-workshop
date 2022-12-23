import os
import sys
import json
import requests
import argparse
import time
import datetime
from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError

from kafka import KafkaAdminClient, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

# http://mtadatamine.s3-website-us-east-1.amazonaws.com/#/subwayRealTimeFeeds
default_feed_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"

parser = argparse.ArgumentParser()
parser.add_argument("--brokers", default="localhost:9092")
parser.add_argument("--topic", default="gtfs_mta_subway")
parser.add_argument("--feed", default=default_feed_url)
parser.add_argument("--api_key")
parser.add_argument("--ref_dir", default="ref/")
parser.add_argument("--enrich", action="store_true")
parser.add_argument("--runtime", type=int, default=60)
args = parser.parse_args()

api_key = args.api_key
if not api_key:
    api_key = os.getenv("MTA_API_KEY")
base_dir = args.ref_dir
if not os.path.isdir(base_dir):
    sys.exit(f"Reference data directory '{base_dir}' does not exist")
print(f"Feed: {args.feed}")

# Load reference data
# http://web.mta.info/developers/data/nyct/subway/google_transit.zip
def load_ref(file):
    ref = {}
    with open(file, mode="r") as ref_file:
        header = [v.strip() for v in ref_file.readline().split(",")]
        for row in ref_file.readlines():
            data = [v.strip() for v in row.split(",")]
            ref[data[0]] = {k: v for k, v in zip(header, data)}
    return ref

# Lookup reference data
def lookup(ref, key, field):
    if not isinstance(ref, dict):
        return None
    entry = dict(ref).get(key, None)
    if entry:
        if not isinstance(entry, dict):
            return None
        value = dict(entry).get(field, None)
        return value

routes = load_ref(f"{base_dir}/routes.txt")
stops = load_ref(f"{base_dir}/stops.txt")

# Create topic
admin = KafkaAdminClient(bootstrap_servers=args.brokers)
try:
    admin.create_topics(
        new_topics=[NewTopic(
            name=args.topic,
            num_partitions=1,
            replication_factor=1
        )])
    print(f"Created topic: {args.topic}")
except TopicAlreadyExistsError as e:
    print(f"Topic already exists: {args.topic}")
finally:
    admin.close()

producer = KafkaProducer(
    bootstrap_servers=args.brokers,
    compression_type="gzip"
)

def on_success(metadata):
  print(f"Sent to topic '{metadata.topic}' at offset {metadata.offset}")

def on_error(e):
  print(f"Error sending message: {e}")

# Runtime
runtime_mins = args.runtime
if runtime_mins < 1:
    runtime_mins = 1
end = datetime.datetime.now() + datetime.timedelta(minutes=runtime_mins)

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
        if not entity.HasField("trip_update"):
            continue
        trip_update = {"id": entity.id}
        tu = entity.trip_update

        trip = {}
        trip["trip_id"] = tu.trip.trip_id
        trip["route_id"] = tu.trip.route_id
        if args.enrich:
            trip["route_long_name"] = lookup(routes, tu.trip.route_id, "route_long_name")
        trip["start_time"] = tu.trip.start_time
        trip["start_date"] = tu.trip.start_date
        trip_update["trip"] = trip

        updates = []
        for stu in tu.stop_time_update:
            update = {"stop_id": stu.stop_id}
            if args.enrich:
                update["stop_name"] = lookup(stops, stu.stop_id, "stop_name")
                update["stop_lat"] = lookup(stops, stu.stop_id, "stop_lat")
                update["stop_lon"] = lookup(stops, stu.stop_id, "stop_lon")
            if stu.HasField("arrival"):
                update["arrival"] = stu.arrival.time
            if stu.HasField("departure"):
                update["departure"] = stu.departure.time
            updates.append(update)
        trip_update["updates"] = updates

        future = producer.send(
            args.topic,
            key=str.encode(entity.id),
            value=json.dumps(trip_update).encode()
        )
        future.add_callback(on_success)
        future.add_errback(on_error)
    time.sleep(2)

producer.flush()
producer.close()
