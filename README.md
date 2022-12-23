# MTA Subway Realtime Feeds

http://mtadatamine.s3-website-us-east-1.amazonaws.com/#/subwayRealTimeFeeds

### Download Reference Data

```bash
curl -L -O http://web.mta.info/developers/data/nyct/subway/google_transit.zip
unzip google_transit.zip -d ref/
```

### Setup Python Environment

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Recreate Protobufs

```bash
protoc --python_out=google/transit --proto_path=proto/ proto/nyct-subway.proto
protoc --python_out=google/transit --proto_path=proto/ proto/gtfs-realtime.proto
```
