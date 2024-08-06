import json
import logging
import os
import time
from abc import ABC
from enum import Enum
from typing import Any, override

import paho.mqtt.client as mqtt
import requests

logging.basicConfig(level=logging.INFO)


class DataType(Enum):
    DATA = "Data"
    INFORMATION = "Information"


status_map: dict[int, str] = {
    0: "Waiting",
    1: "Checking",
    2: "Normal",
    3: "Off",
    4: "Permanent Fault",
    5: "Updating",
    6: "EPS Check",
    7: "EPS Mode",
    8: "Self Test",
    9: "Idle",
    10: "Standby",
}


class Entity(ABC):
    def __init__(
        self,
        name: str,
        device_class: str | None,
        icon: str,
        idx: float,
        factor: int,
        unit: str | None,
        data_type: DataType = DataType.DATA,
    ):
        self.id = "solax_" + name.replace(" ", "_").replace("-", "").lower()
        self.topic = f"homeassistant/sensor/{self.id}/state"
        self.config_topic = f"homeassistant/sensor/{self.id}/config"
        self.state_class = "measurement"
        self.name = name
        self.device_class = device_class
        self.icon = icon
        self.unit = unit
        self.idx = idx
        self.factor = factor
        self._state = 0
        self.data_type = data_type

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value[self.data_type.value][self.idx] / self.factor

    @property
    def ha_config(self) -> dict:
        config = {
            "state_topic": self.topic,
            "name": self.name,
            "unique_id": self.id,
            "icon": self.icon,
            "device_class": self.device_class if self.device_class else None,
            "state_class": self.state_class,
            "unit_of_measurement": self.unit if self.unit else None,
            "device": {
                "identifiers": ["Solax_X1_Mini_G3"],
                "name": "SolaX",
                "model": "X1 Mini G3",
                "manufacturer": "SolaX",
                "suggested_area": "Garage",
            },
        }

        return config


class EnergyEntity(Entity):
    def __init__(
        self,
        name: str,
        icon: str,
        idx: float,
        factor: int,
    ):
        super().__init__(name, "energy", icon, idx, factor, "kWh")
        self.state_class = "total_increasing"


class PowerEntity(Entity):
    def __init__(self, name: str, icon: str, idx: float):
        super().__init__(name, "power", icon, idx, 1, "W")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        v = value[self.data_type.value][self.idx] / self.factor
        self._state = v if v < 32768 else v - 65536


class FrequencyEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, "frequency", "mdi:music-clef-treble", idx, 100, "Hz")


class VoltageEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, "voltage", "mdi:current-ac", idx, 10, "V")


class CurrentEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, "current", "mdi:current-ac", idx, 10, "A")


class TemperatureEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, "temperature", "mdi:thermometer", idx, 1, "°C")


class StatusEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, None, "mdi:check", idx, 1, None)
        self.state_class = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        v = value[self.data_type.value][self.idx] / self.factor
        self._state = status_map.get(v, "Unknown")


class PowerCalcEntity(PowerEntity):
    def __init__(self, name: str, icon: str, idx1: float, idx2: float):
        super().__init__(name, icon, idx1)
        self.id = name.replace(" ", "_").replace("-", "").lower()
        self.topic = f"homeassistant/sensor/{self.id}/state"
        self.config_topic = f"homeassistant/sensor/{self.id}/config"
        self.idx2 = idx2

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        ac = value[self.data_type.value][self.idx] / self.factor
        feedin_aux = value[self.data_type.value][self.idx2] / self.factor
        feedin_power = feedin_aux if feedin_aux < 32768 else feedin_aux - 65536
        self._state = ac - feedin_power

    @override
    @property
    def ha_config(self) -> dict:
        config = super().ha_config
        config["object_id"] = self.id
        return config


class VersionEntity(Entity):
    def __init__(self, name: str, idx: float):
        super().__init__(name, None, "mdi:sync", idx, 1, None, DataType.INFORMATION)

    @override
    @property
    def ha_config(self) -> dict:
        config = super().ha_config
        config["entity_category"] = "diagnostic"
        return config


entities = [
    TemperatureEntity("Inverter Temperature", 55),
    EnergyEntity("Energy Today", "mdi:solar-panel", 13, 10),
    EnergyEntity("Energy Total", "mdi:chart-line", 11, 10),
    VoltageEntity("DC Voltage 1", 3),
    CurrentEntity("DC Current 1", 5),
    PowerEntity("DC Power 1", "mdi:power-socket-de", 7),
    VoltageEntity("AC Output Voltage", 0),
    CurrentEntity("AC Current", 1),
    PowerEntity("AC Power", "mdi:solar-panel", 2),
    FrequencyEntity("AC Frequency", 9),
    status := StatusEntity("Inverter Operation Mode", 10),
    PowerEntity("Feed-in Power", "mdi:transmission-tower", 48),
    EnergyEntity("Feed-in Energy", "mdi:home-export-outline", 50, 100),
    EnergyEntity("Consume Energy", "mdi:home-import-outline", 52, 100),
    VersionEntity("Inverter Version DSP", 4),
    VersionEntity("Inverter Version ARM", 6),
    PowerCalcEntity("Home Consumption Power", "mdi:home", 2, 48),
]


def fetch_solax_data(ip: str, password: str) -> dict | None:
    try:
        response = requests.post(
            f"http://{ip}", data=f"?optType=ReadRealTimeData&pwd={password}", timeout=5
        )
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        return None
    except Exception as err:
        logging.error(f"SolaX request error: {type(err)}")
        return None


def connect_mqtt(
    broker: str,
    username: str = None,
    password: str = None,
) -> mqtt.Client | None:
    client = mqtt.Client()
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    if username and password:
        client.username_pw_set(username, password)
    try:
        client.connect(broker)
        return client
    except Exception as err:
        logging.error(f"MQTT connection error: {err}")
        return None


def publish_to_mqtt(client: mqtt.Client, topic: str, value: Any, retain: bool = False):
    try:
        client.publish(topic, value, retain=retain)
    except Exception as err:
        logging.error(f"MQTT publish error: {err}")


if __name__ == "__main__":
    solax_ip = os.environ.get("SOLAX_IP")
    solax_password = os.environ.get("SOLAX_PASSWORD")
    mqtt_ip = os.environ.get("MQTT_IP")
    mqtt_username = os.environ.get("MQTT_USERNAME")
    mqtt_password = os.environ.get("MQTT_PASSWORD")
    time_delay = int(os.environ.get("TIME_DELAY", 5))
    offline_delay = int(os.environ.get("OFFLINE_DELAY", 60))

    client = connect_mqtt(mqtt_ip, mqtt_username, mqtt_password)

    if client is None:
        exit(1)

    # Configure MQTT Discovery in Home Assistant
    for entity in entities:
        publish_to_mqtt(
            client,
            entity.config_topic,
            json.dumps(entity.ha_config),
            retain=True,
        )

    retries = 0

    while True:
        try:
            data = fetch_solax_data(solax_ip, solax_password)

            if data is None:
                if (retries := retries + 1) > 3:
                    logging.info(
                        f"Inverter is offline. Retrying in {offline_delay} seconds."
                    )
                    publish_to_mqtt(client, status.topic, "Offline")
                    time.sleep(offline_delay)
                    continue
            else:
                retries = 0
                if data["Data"][50] == 0 and data["Data"][52] == 0:
                    logging.info(
                        f"Inverter is initializing. Retrying in {offline_delay} seconds."
                    )
                    time.sleep(offline_delay)
                    continue
                for entity in entities:
                    entity.state = data
                    publish_to_mqtt(client, entity.topic, entity.state)
            time.sleep(time_delay)
        except KeyboardInterrupt:
            break

    client.disconnect()
