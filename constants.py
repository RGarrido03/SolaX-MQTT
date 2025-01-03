from enum import Enum

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

class DataType(Enum):
    DATA = "Data"
    INFORMATION = "Information"

