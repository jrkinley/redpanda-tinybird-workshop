import os.path
import json
import argparse
import time
import mta_utils as utils

from kafka import KafkaProducer
from mta_reference import MTAReference

parser = argparse.ArgumentParser()
parser.add_argument("--brokers", default="localhost:9092")
parser.add_argument("--topic", default="gtfs_mta_subway")
parser.add_argument("--file", required=True)
args = parser.parse_args()

if not os.path.isfile(args.file):
    raise FileNotFoundError(f"File does not exist: {args.file}")
print(f"File: {args.file}")

utils.create_topic(args.brokers, args.topic)
producer = KafkaProducer(
    bootstrap_servers=args.brokers,
    compression_type="gzip"
)

def on_success(metadata):
    print(f"Sent to topic '{metadata.topic}' at offset {metadata.offset}")

def on_error(e):
    print(f"Error sending message: {e}")

with open(args.file, "r") as file:
    for line in file:
        message = json.loads(line)
        print(message)
        future = producer.send(
            args.topic,
            key=str.encode(message["id"]),
            value=json.dumps(message).encode()
        )
        future.add_callback(on_success)
        future.add_errback(on_error)
        time.sleep(0.2)

producer.flush()
producer.close()
