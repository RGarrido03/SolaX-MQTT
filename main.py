import json
import logging
import os
import time

from entities import *
from mqtt import connect_mqtt, publish_to_mqtt
from request import fetch_solax_data

logging.basicConfig(level=logging.INFO)


entities = [
    TemperatureEntity("Inverter Temperature", 55),
    EnergyEntity("Energy Today", "mdi:solar-panel", 13, 10),
    EnergyEntity("Energy Total", "mdi:chart-line", 11, 10, skip_init=True),
    PowerEntity("AC Power", "mdi:solar-panel", 2),
    StatusEntity("Inverter Operation Mode", 10),
    VersionEntity("Inverter Version DSP", 4),
    VersionEntity("Inverter Version ARM", 6),
]


solax_ip = os.environ.get("SOLAX_IP")
solax_password = os.environ.get("SOLAX_PASSWORD")
mqtt_ip = os.environ.get("MQTT_IP")
mqtt_username = os.environ.get("MQTT_USERNAME")
mqtt_password = os.environ.get("MQTT_PASSWORD")
time_delay = int(os.environ.get("TIME_DELAY", 5))
offline_delay = int(os.environ.get("OFFLINE_DELAY", 60))

client = connect_mqtt(mqtt_ip, mqtt_username, mqtt_password)

# Configure MQTT Discovery in Home Assistant
for entity in entities:
    publish_to_mqtt(
        client,
        entity.config_topic,
        json.dumps(entity.ha_config),
        retain=True,
    )

retries = 0
initialized = False

while True:
    try:
        data = fetch_solax_data(solax_ip, solax_password)

        if data is None:
            if (retries := retries + 1) == 3 and initialized:
                logging.info("Inverter is offline")
                for entity in entities:
                    publish_to_mqtt(
                        client, entity.topic, entity.fallback_state, retain=True
                    )
            time.sleep(time_delay if retries < 3 else offline_delay)
            continue

        if retries > 0:
            logging.info("Inverter is online")
        retries = 0
        initialized = True

        for entity in entities:
            try:
                entity.state = data
                publish_to_mqtt(client, entity.topic, entity.state)
            except ValueError:
                logging.warning(f"Skipping {entity.name} initialization value")
        time.sleep(time_delay)
    except KeyboardInterrupt:
        client.disconnect()
        break
