from abc import ABC
from typing import override

from constants import DataType, status_map


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
        skip_init: bool = False,
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
        self.skip_init = skip_init

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value[self.data_type.value][self.idx] / self.factor
        if self.skip_init and self._state == 0:
            raise ValueError("Initialization value")

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
        skip_init: bool = False,
    ):
        super().__init__(name, "energy", icon, idx, factor, "kWh", skip_init=skip_init)
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
    def __init__(self, name: str, idx: float, skip_init: bool = False):
        super().__init__(
            name,
            "frequency",
            "mdi:music-clef-treble",
            idx,
            100,
            "Hz",
            skip_init=skip_init,
        )


class VoltageEntity(Entity):
    def __init__(self, name: str, idx: float, skip_init: bool = False):
        super().__init__(
            name, "voltage", "mdi:current-ac", idx, 10, "V", skip_init=skip_init
        )


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
