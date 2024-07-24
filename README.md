# SolaX polling to MQTT

This script polls a SolaX inverter for its current status and publishes it to an MQTT broker.
The default time between polls is 5 seconds, although this can be changed.

## Installation
This script is Dockerized, so you can run it in a container, without dealing with dependencies.

### Docker
1. Clone this repository
2. Use the provided `compose.yaml` file as a base
3. Change the environment variables to match your setup
4. Run `docker compose up -d`

### Manual
1. Clone this repository
2. Create a virtual environment
3. Install the required dependencies with `pip install -r requirements.txt`
4. Run the script with `python solax.py`

## Configuration
The script requires the following environment variables to be set:

| Environment variable | Description                          |
|----------------------|--------------------------------------|
| `SOLAX_IP`           | IP of the SolaX inverter             |
| `SOLAX_PASSWORD`     | Inverter password (i.e., the SN)     |
| `MQTT_IP`            | IP of the MQTT broker                |
| `MQTT_USERNAME`      | Username of MQTT broker              |
| `MQTT_PASSWORD`      | Password of MQTT broker              |
| `TIME_DELAY`         | Interval between polls (default: 5s) |
