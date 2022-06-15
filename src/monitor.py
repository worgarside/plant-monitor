"""Monitors plant soil moisture and sends it to Home Assistant"""
from datetime import datetime
from json import dumps
from logging import getLogger, DEBUG
from os import getenv, environ
from os.path import join
from pathlib import Path
from time import sleep

from dotenv import load_dotenv, dotenv_values
from paho.mqtt.publish import multiple
from wg_utilities.functions import force_mkdir
from wg_utilities.loggers import add_stream_handler, add_file_handler

from plant import TEST_MODE, PLANTS

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


def check_for_limit_updates():
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


def main():
    """Send Home Assistant readings every 30 seconds"""
    if not TEST_MODE:
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
        check_for_limit_updates()


if __name__ == "__main__":
    main()
