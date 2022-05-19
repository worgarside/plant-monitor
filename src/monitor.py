"""Monitors plant soil moisture and sends it to Home Assistant"""
from json import dumps
from os import getenv
from time import sleep
from paho.mqtt.publish import multiple
from dotenv import load_dotenv

from plant import Plant, TEST_MODE


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
        (("Monstera", 0.8, 7.54), ("Yukka", 3.4, 10.8), ("Succulent", 4, 7))
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
        print(dumps(msgs, indent=4))
        sleep(30)


if __name__ == "__main__":
    main()
