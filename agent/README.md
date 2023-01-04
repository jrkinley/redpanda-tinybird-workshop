### Setup Local Test

```bash
cd redpanda-tinybird-edge/agent

# Download edge agent
curl -L -O https://github.com/redpanda-data/redpanda-edge-agent/releases/download/v22.1.0/redpanda-edge-agent-linux-amd64-22.1.0.tar.gz
tar xvf redpanda-edge-agent-linux-amd64-22.1.0.tar.gz

# Spin up source and destination containers
docker-compose up -d
docker exec redpanda_source tail -100f /var/lib/redpanda/data/agent.log

# Open a new terminal and generate GTFS data
# Sign up for an access key at: http://mtadatamine.s3-website-us-east-1.amazonaws.com
cd redpanda-tinybird-edge
source env/bin/activate
python mta_subway_produce.py \
  --brokers localhost:19092 \
  --topic gtfs_mta_subway_enriched \
  --api_key <access key>
  --enrich \
  --runtime 10

# Open a new terminal and consume from the destination cluster
cd redpanda-tinybird-edge
rpk topic consume gtfs_mta_subway_enriched --brokers localhost:29092
```