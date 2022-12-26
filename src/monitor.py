"""Monitors plant soil moisture and sends it to Home Assistant"""
from __future__ import annotations

from datetime import datetime
from json import dumps
from logging import DEBUG, getLogger
from os import environ, getenv
from os.path import join
from pathlib import Path
from time import sleep
from typing import Any

from dotenv import dotenv_values, load_dotenv
from paho.mqtt.client import Client, MQTTMessage
from wg_utilities.exceptions import on_exception  # pylint: disable=no-name-in-module
from wg_utilities.functions import force_mkdir
from wg_utilities.loggers import add_file_handler, add_stream_handler

from plant import PLANT_NAMES, TEST_MODE, Plant

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

add_file_handler(
    LOGGER,
    logfile_path=force_mkdir(
        join(
            Path.home(),
            "logs",
            "plant-monitor",
            f"{datetime.today().strftime('%Y-%m-%d')}.log",
        ),
        path_is_file=True,
    ),
)
add_stream_handler(LOGGER)


load_dotenv()


PLANTS = [
    Plant(name=plant_name, sensor_number=i + 1, pump_number=i + 1)
    for i, plant_name in enumerate(PLANT_NAMES)
]

WATER_TOPICS = {plant.water_mqtt_topic: plant for plant in PLANTS}

MQTT_CLIENT = Client()
MQTT_CLIENT.username_pw_set(
    username=getenv("MQTT_USERNAME"), password=getenv("MQTT_PASSWORD")
)


@on_exception()  # type: ignore[misc]
def check_for_limit_updates() -> None:
    """Re-load the env vars, check for updated Plant limits, and update plants
    accordingly
    """
    new_env_vars = dotenv_values()
    old_env_vars = environ.copy()

    for plant in PLANTS:
        update_plant = False
        for point_type in ("dry", "wet"):
            env_var_key = f"{plant.name}_{point_type}_POINT".upper()

            update_plant |= old_env_vars.get(env_var_key) != new_env_vars.get(
                env_var_key
            )

        if update_plant:
            load_dotenv(override=True)
            plant.get_limits_from_env_vars()


# noinspection PyIncorrectDocstring
@on_exception()  # type: ignore[misc]
def on_message(_: Any, __: Any, message: MQTTMessage) -> None:
    """Callback method for watering the plants on MQTT message

    Args:
        message (MQTTMessage): the message object from the MQTT subscription
    """

    LOGGER.debug("Received '%s' on topic '%s'", message.payload.decode(), message.topic)

    WATER_TOPICS[message.topic].water(float(message.payload.decode()))


@on_exception()  # type: ignore[misc]
def setup_mqtt_client() -> None:
    """Run setup for MQTT client"""

    MQTT_CLIENT.connect(host=getenv("MQTT_HOST"))

    for topic in WATER_TOPICS.keys():
        MQTT_CLIENT.subscribe(topic)
        LOGGER.debug("Subscribed to `%s`", topic)

    MQTT_CLIENT.on_message = on_message
    MQTT_CLIENT.loop_start()


@on_exception()  # type: ignore[misc]
def main() -> None:
    """Send Home Assistant readings every 30 seconds"""
    if not TEST_MODE:
        sleep(5)  # let the sensor initialise

    setup_mqtt_client()

    while True:
        for plant in PLANTS:
            message = {
                "topic": f"/will_s_room/plants/{plant.name.lower()}",
                "payload": plant.home_assistant_payload,
            }

            LOGGER.debug(dumps(message))
            if not TEST_MODE:
                MQTT_CLIENT.publish(**message)

        sleep(30)
        check_for_limit_updates()


if __name__ == "__main__":
    main()
