"""Classes for use in the monitor"""

from json import dumps
from logging import getLogger, DEBUG
from os import getenv
from random import randint

from wg_utilities.functions import try_float  # pylint: disable=no-name-in-module

try:
    from grow.moisture import Moisture

    TEST_MODE = False
except ModuleNotFoundError:
    TEST_MODE = True

    class Moisture:
        """Dummy class for running this on a non-Pi machine"""

        def __init__(self, *_, **__):
            pass

        def set_wet_point(self, _):
            """Dummy function"""

        def set_dry_point(self, _):
            """Dummy function"""

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


LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)


class Plant:
    """Class for monitoring (and watering, soon) plants

    Args:
        sensor_number (int): the channel the sensor is plugged into on the hat
        name (str): the name of the plant
        wet_point (float): the moisture value at which the soil is considered wet
        dry_point (float): the moisture value at which the soil is considered dry

    """

    SENSOR_ATTRIBUTES = ("moisture", "saturation")

    def __init__(
        self,
        sensor_number,
        name,
        wet_point=None,
        dry_point=None,
        get_limits_from_env_vars=True,
    ):
        self.name = name

        self.moisture_sensor = Moisture(
            sensor_number, wet_point=wet_point, dry_point=dry_point
        )

        if get_limits_from_env_vars is True:
            if not (wet_point is None and dry_point is None):
                LOGGER.warning(
                    "`get_limits_from_env_vars` arg is True, "
                    "wet/dry point arguments will be ignored"
                )
            self.get_limits_from_env_vars()
        else:
            self.moisture_sensor.set_wet_point(wet_point)
            self.moisture_sensor.set_dry_point(dry_point)

    def get_limits_from_env_vars(self):
        """Get the wet/dry point limits from the environment"""

        if (
            wet_point := try_float(getenv(f"{self.name.upper()}_WET_POINT"), None)
        ) is not None:
            LOGGER.debug("Setting %s wet point to %s", self.name, wet_point)
            self.moisture_sensor.set_wet_point(wet_point)

        if (
            dry_point := try_float(getenv(f"{self.name.upper()}_DRY_POINT"), None)
        ) is not None:
            LOGGER.debug("Setting %s dry point to %s", self.name, dry_point)
            self.moisture_sensor.set_dry_point(dry_point)

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
