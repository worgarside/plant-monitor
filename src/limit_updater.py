"""Subscribes to an MQTT topic, so HA can push updates to the limits"""
from datetime import datetime
from logging import DEBUG, getLogger
from os import getenv
from os.path import join
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv, set_key
from paho.mqtt.client import MQTTMessage
from paho.mqtt.subscribe import callback
from wg_utilities.exceptions import on_exception  # pylint: disable=no-name-in-module
from wg_utilities.functions import force_mkdir
from wg_utilities.loggers import add_file_handler, add_stream_handler

from plant import LOGGER as PLANT_LOGGER
from plant import PLANTS

DOTENV_PATH = find_dotenv()
load_dotenv(DOTENV_PATH)

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)
LOGFILE = f"{datetime.today().strftime('%Y-%m-%d')}.log"
add_file_handler(
    LOGGER,
    logfile_path=force_mkdir(
        join(
            Path.home(),
            "logs",
            "limit_updater",
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
            "limit_updater",
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

TOPICS = [plant.dry_point_set_mqtt_topic for plant in PLANTS] + [
    plant.wet_point_set_mqtt_topic for plant in PLANTS
]


# noinspection PyIncorrectDocstring
@on_exception()  # type: ignore[misc]
def on_message(_: Any, __: Any, message: MQTTMessage) -> None:
    """Callback method for updating env vars on MQTT message

    Args:
        message (MQTTMessage): the message object from the MQTT subscription
    """

    _, _, plant_name, point_type, _ = message.topic.split("/")

    ev_name = f"{plant_name.upper()}_{point_type.upper()}"
    value = message.payload.decode()

    LOGGER.debug("Setting %s to %s", ev_name, value)
    set_key(
        DOTENV_PATH,
        ev_name,
        value,
    )


LOGGER.info("Listening on topics:    \n%s", "    \n".join(TOPICS))
callback(on_message, TOPICS, **MQTT_AUTH_KWARGS)
