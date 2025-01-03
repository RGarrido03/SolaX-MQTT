import logging

import requests


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
