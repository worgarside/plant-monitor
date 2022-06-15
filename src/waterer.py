"""Subscribes to an MQTT topic, so watering can be done from HA"""
from datetime import datetime
from logging import getLogger, DEBUG
from os import getenv
from os.path import join
from pathlib import Path

from dotenv import load_dotenv
from paho.mqtt.subscribe import callback
from wg_utilities.functions import force_mkdir
from wg_utilities.loggers import add_file_handler, add_stream_handler

from plant import PLANTS, LOGGER as PLANT_LOGGER

load_dotenv()

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)
LOGFILE = f"{datetime.today().strftime('%Y-%m-%d')}.log"
add_file_handler(
    LOGGER,
    logfile_path=force_mkdir(
        join(
            Path.home(),
            "logs",
            "waterer",
            LOGFILE,
        ),
        path_is_file=True,
    ),
)
add_file_handler(
    PLANT_LOGGER,
    logfile_path=force_mkdir(
        join(
            Path.home(),
            "logs",
            "waterer",
            LOGFILE,
        ),
        path_is_file=True,
    ),
)
add_stream_handler(LOGGER)

MQTT_AUTH_KWARGS = dict(
    hostname=getenv("MQTT_HOST"),
    auth={
        "username": getenv("MQTT_USERNAME"),
        "password": getenv("MQTT_PASSWORD"),
    },
)

TOPICS = {plant.water_mqtt_topic: plant for plant in PLANTS}


# noinspection PyIncorrectDocstring
def on_message(_, __, message):
    """Callback method for watering the plants on MQTT message

    Args:
        message (MQTTMessage): the message object from the MQTT subscription
    """

    LOGGER.debug("Received '%s' on topic '%s'", message.payload.decode(), message.topic)

    TOPICS[message.topic].water(float(message.payload.decode()))


LOGGER.info("Listening on topics:    \n%s", "    \n".join(list(TOPICS.keys())))
callback(on_message, list(TOPICS.keys()), **MQTT_AUTH_KWARGS)
