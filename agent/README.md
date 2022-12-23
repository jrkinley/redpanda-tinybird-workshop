### Setup Local Test

```bash
cd agent

# Download edge agent
curl -L -O https://github.com/redpanda-data/redpanda-edge-agent/releases/download/v22.1.0/redpanda-edge-agent-linux-amd64-22.1.0.tar.gz
tar xvf redpanda-edge-agent-linux-amd64-22.1.0.tar.gz

# Spin up source and destination containers
docker-compose up -d
docker exec redpanda_source tail -100f /var/lib/redpanda/data/agent.log

# Generate GTFS data
cd ..
source env/bin/activate
python mta-subway-producer.py --brokers localhost:19092 --topic gtfs_mta_subway_enriched --enrich --runtime 10

# Consume from the destination cluster
rpk topic consume gtfs_mta_subway_enriched --brokers localhost:29092
```