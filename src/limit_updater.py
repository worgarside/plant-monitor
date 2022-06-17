"""Subscribes to an MQTT topic, so HA can push updates to the limits"""
from os import getenv
from typing import Any

from dotenv import find_dotenv, load_dotenv, set_key
from paho.mqtt.client import MQTTMessage
from paho.mqtt.subscribe import callback

from plant import PLANTS

DOTENV_PATH = find_dotenv()
load_dotenv(DOTENV_PATH)

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
def on_message(_: Any, __: Any, message: MQTTMessage) -> None:
    """Callback method for updating env vars on MQTT message

    Args:
        message (MQTTMessage): the message object from the MQTT subscription
    """

    _, _, plant_name, point_type, _ = message.topic.split("/")
    set_key(
        DOTENV_PATH,
        f"{plant_name.upper()}_{point_type.upper()}",
        message.payload.decode(),
    )


callback(on_message, TOPICS, **MQTT_AUTH_KWARGS)
