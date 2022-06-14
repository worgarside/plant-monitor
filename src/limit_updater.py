"""Subscribes to an MQTT topic, so HA can push updates to the limits"""
from os import getenv

from dotenv import load_dotenv, find_dotenv, set_key
from paho.mqtt.subscribe import callback

DOTENV_PATH = find_dotenv()
load_dotenv(DOTENV_PATH)

MQTT_AUTH_KWARGS = dict(
    hostname=getenv("MQTT_HOST"),
    auth={
        "username": getenv("MQTT_USERNAME"),
        "password": getenv("MQTT_PASSWORD"),
    },
)

TOPICS = [
    f"/plant_monitor/{plant}/{point_type}_point/set"
    for plant in ("monstera", "yukka", "ficus")
    for point_type in ("dry", "wet")
]


# noinspection PyIncorrectDocstring
def on_message(_, __, message):
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
