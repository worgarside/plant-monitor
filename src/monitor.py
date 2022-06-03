"""Monitors plant soil moisture and sends it to Home Assistant"""
from datetime import datetime
from json import dumps
from logging import getLogger, DEBUG
from os import getenv
from os.path import join
from pathlib import Path
from time import sleep
from paho.mqtt.publish import multiple
from dotenv import load_dotenv
from wg_utilities.functions import (  # pylint: disable=no-name-in-module
    force_mkdir,
    try_float,
)
from wg_utilities.loggers import add_stream_handler, add_file_handler

from plant import Plant, TEST_MODE


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

MQTT_AUTH_KWARGS = dict(
    hostname=getenv("MQTT_HOST"),
    auth={
        "username": getenv("MQTT_USERNAME"),
        "password": getenv("MQTT_PASSWORD"),
    },
)

PLANTS = [
    Plant(i + 1, *plant)
    for i, plant in enumerate(
        (
            (
                "Monstera",
                try_float(getenv("MONSTERA_WET_POINT"), None),
                try_float(getenv("MONSTERA_DRY_POINT"), None),
            ),
            (
                "Yukka",
                try_float(getenv("YUKKA_WET_POINT"), None),
                try_float(getenv("YUKKA_DRY_POINT"), None),
            ),
            (
                "Succulent",
                try_float(getenv("SUCCULENT_WET_POINT"), None),
                try_float(getenv("SUCCULENT_DRY_POINT"), None),
            ),
        )
    )
]


def main():
    """Send Home Assistant readings every 30 seconds"""
    sleep(5)  # let the sensor initialise

    while True:
        msgs = [
            {
                "topic": f"/will_s_room/plants/{plant.name.lower()}",
                "payload": plant.home_assistant_payload,
            }
            for plant in PLANTS
        ]
        if not TEST_MODE:
            multiple(
                msgs,
                **MQTT_AUTH_KWARGS,
            )
        LOGGER.debug(dumps(msgs))
        sleep(30)


if __name__ == "__main__":
    main()
