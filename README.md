# MTA Subway Realtime Feeds

Here you'll find the code used for the [Streaming Data at the Edge](https://go.redpanda.com/virtual-workshop-january2023) virtual workshop. In a nutshell the workshop deploys the following solution:

1. Install [Redpanda](https://redpanda.com/) on ARM-based EC2 instances
2. Install [Redpanda Edge Agent](https://github.com/redpanda-data/redpanda-edge-agent) alongside Redpanda
3. Connect to the [MTA Realtime Feeds](http://mtadatamine.s3-website-us-east-1.amazonaws.com/#/subwayRealTimeFeeds) from each EC2 instance to capture live NYC subway location data and write it to the local Redpanda instance. The idea here is that this simulates data being generated by a moving vehicle that is likely to drop in and out of cellular connectivity. The data needs to be stored while the vehicle is offline and until it reconnects and the data can be forwarded to a central system
4. Configure the Agents to forward messages from the local Redpanda instance to a central Redpanda Cloud cluster
5. Connect [Tinybird](https://www.tinybird.co/) to the central Redpanda Cloud cluster and generate realtime data products

## Deploy

```shell
# Spin up EC2 instances
# Use ARM-based (Graviton2) instances (e.g. c6g.medium)
ssh -i <Key pair name>.pem ec2-user@<Public IPv4 address>

# Install git and clone the workshop repo
sudo yum update -y
sudo yum install git -y
git clone https://github.com/jrkinley/redpanda-tinybird-workshop.git

# Install Redpanda
cd redpanda-tinybird-workshop
curl -1sLf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.rpm.sh' | sudo -E bash
sudo yum install redpanda -y
sudo systemctl start redpanda
sudo systemctl status redpanda

# Install Redpanda Edge Agent
curl -L -O https://github.com/redpanda-data/redpanda-edge-agent/releases/download/v22.1.0/redpanda-edge-agent-linux-arm64-22.1.0.tar.gz
tar xvf redpanda-edge-agent-linux-arm64-22.1.0.tar.gz
sudo mv redpanda-edge-agent /usr/bin/
sudo chown root:ec2-user /usr/bin/redpanda-edge-agent
sudo chmod 770 /usr/bin/redpanda-edge-agent

# Configure the Agent
sudo vim /etc/redpanda/agent.yaml

    id: "nyct-gtfs"
    create_topics: true
    source:
      name: "redpanda-device"
      bootstrap_servers: 127.0.0.1:9092
      topics:
        - gtfs_mta_subway
    destination:
      name: "redpanda-cloud"
      bootstrap_servers: seed...cloud.redpanda.com:9092
      tls:
        enabled: true
      sasl:
        sasl_method: "SCRAM-SHA-256"
        sasl_username: "..."
        sasl_password: "..."

# Start the Agent
sudo mkdir /var/log/redpanda
sudo chown root:ec2-user /var/log/redpanda
sudo chmod 770 /var/log/redpanda
nohup redpanda-edge-agent -config /etc/redpanda/agent.yaml -loglevel debug &> /var/log/redpanda/redpanda-edge-agent.log &
tail -100f /var/log/redpanda/redpanda-edge-agent.log

# Connect to the MTA Realtime Feeds
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

python mta_subway_produce.py \
  --brokers 127.0.0.1:9092 \
  --topic gtfs_mta_subway \
  --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace \
  --api_key ...

# https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs
# https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm
# https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace
# https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw
```

## Console Filters

```javascript
// Broadway Express Route
return value.trip.route_id == "Q"

// Has train stopped at Lexington Av?
var stopped = false
for (const update of value.updates) {
    if (update.stop_id == "B08S") {
        stopped = true
    }
}
return stopped
```

## Reference Data

```shell
curl -L -O http://web.mta.info/developers/data/nyct/subway/google_transit.zip
unzip google_transit.zip -d ref/
```

## Recreate Protobufs

```shell
protoc --python_out=google/transit --proto_path=proto/ proto/nyct-subway.proto
protoc --python_out=google/transit --proto_path=proto/ proto/gtfs-realtime.proto
```
