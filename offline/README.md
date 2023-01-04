### Backup data in case the live feed is unavailable

```bash
source env/bin/activate
export MTA_API_KEY=...

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace \
    --output offline/nyct-gtfs-ace.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm \
    --output offline/nyct-gtfs-bdfm.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g \
    --output offline/nyct-gtfs-g.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz \
    --output offline/nyct-gtfs-jz.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw \
    --output offline/nyct-gtfs-nqrw.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l \
    --output offline/nyct-gtfs-l.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs \
    --output offline/nyct-gtfs-1234567.log \
    --runtime 30

python mta_offline_collect.py \
    --feed https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si \
    --output offline/nyct-gtfs-si.log \
    --runtime 30
```