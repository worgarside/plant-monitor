"""Classes for use in the monitor"""

from json import dumps
from random import randint

try:
    from grow.moisture import Moisture

    TEST_MODE = False
except ModuleNotFoundError:
    from unittest.mock import MagicMock, Mock

    TEST_MODE = True

    class Moisture:
        """Dummy class for running this on a non-Pi machine"""

        def __init__(self, *_, **__):
            pass

        @property
        def moisture(self):
            """
            Returns:
                int: random integer for fake moisture reading
            """
            return randint(0, 900)

        @property
        def saturation(self):
            """
            Returns:
                float: random float for fake saturation reading
            """
            return round(randint(0, 10000) / 100)


class Plant:
    """Class for monitoring (and watering, soon) plants

    Args:
        sensor_number (int): the channel the sensor is plugged into on the hat
        name (str): the name of the plant
        wet_point (float): the moisture value at which the soil is considered wet
        dry_point (float): the moisture value at which the soil is considered dry

    """

    SENSOR_ATTRIBUTES = ("moisture", "saturation")

    def __init__(self, sensor_number, name, wet_point=0.7, dry_point=26.7):
        self.name = name
        self.moisture_sensor = Moisture(
            sensor_number, wet_point=wet_point, dry_point=dry_point
        )

    @property
    def home_assistant_payload(self):
        """
        Returns:
            str: a payload for Home Assistant with the relevant readings
        """
        return dumps(
            {
                attr_name: getattr(self, attr_name)
                for attr_name in self.SENSOR_ATTRIBUTES
            }
        )

    @property
    def moisture(self):
        """Return the raw moisture level. The value returned is the pulses/sec read
         from the soil moisture sensor.

        Returns:
            Union[str, float]: the moisture level, or a default if it's unknown
        """
        if (moisture := self.moisture_sensor.moisture) in (0, 1):
            return "unknown"

        return round(moisture, 6)

    @property
    def saturation(self):
        """Return saturation as a float from 0.0 to 1.0. This value is calculated
         using the wet and dry points.

        Returns:
            Union[str, float]: the saturation level, or a default if it's unknown
        """
        if (saturation := self.moisture_sensor.saturation) in (0, 1):
            return "unknown"

        return round(saturation * 100, 3)

    def __str__(self):
        return f"{self.name}:\t{self.moisture}"
