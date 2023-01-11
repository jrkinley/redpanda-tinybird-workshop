from datetime import datetime as dt
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
from mta_reference import MTAReference

def create_topic(brokers, topic, partitions=1, replicas=1):
    admin = KafkaAdminClient(bootstrap_servers=brokers)
    try:
        admin.create_topics(
            new_topics=[NewTopic(
                name=topic,
                num_partitions=partitions,
                replication_factor=replicas
            )])
        print(f"Created topic: {topic}")
    except TopicAlreadyExistsError as e:
        print(f"Topic already exists: {topic}")
    finally:
        admin.close()

def parse_entity(entity, enrich=False, ref=None):
    if not entity.HasField("trip_update"):
        return None
    if not isinstance(enrich, bool):
        raise TypeError("enrich must be a bool")
    if enrich is True:
        if not isinstance(ref, MTAReference):
            raise TypeError("ref must be of type MTAReference")

    trip_update = {"id": entity.id}
    tu = entity.trip_update

    trip = {}
    trip["trip_id"] = tu.trip.trip_id
    trip["route_id"] = tu.trip.route_id
    if enrich:
        trip["route_long_name"] = ref.lookup_route(tu.trip.route_id, "route_long_name")
    # trip["start_time"] = tu.trip.start_time
    start_date = dt.strptime(tu.trip.start_date, "%Y%m%d").strftime("%Y-%m-%d")
    if tu.trip.start_time != "":
        start_date += " " + start_date
    trip["start_date"] = start_date
    trip_update["trip"] = trip

    updates = []
    for stu in tu.stop_time_update:
        update = {"stop_id": stu.stop_id}
        if enrich:
            update["stop_name"] = ref.lookup_stop(stu.stop_id, "stop_name")
            update["stop_lat"] = ref.lookup_stop(stu.stop_id, "stop_lat")
            update["stop_lon"] = ref.lookup_stop(stu.stop_id, "stop_lon")
        if stu.HasField("arrival"):
            update["arrival"] = stu.arrival.time
        if stu.HasField("departure"):
            update["departure"] = stu.departure.time
        updates.append(update)
    trip_update["updates"] = updates
    return trip_update
