"""Classes for use in the monitor."""

from __future__ import annotations

from json import dumps
from logging import DEBUG, getLogger
from os import getenv
from random import randint

from dotenv import load_dotenv
from wg_utilities.exceptions import on_exception
from wg_utilities.functions import try_float
from wg_utilities.loggers import add_stream_handler

load_dotenv()

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)
add_stream_handler(LOGGER)

try:
    from grow.moisture import Moisture
    from grow.pump import Pump

    TEST_MODE = False
except ModuleNotFoundError:
    TEST_MODE = True

    LOGGER.warning("Unable to import GrowHat dependencies, running in test mode")

    class Moisture:  # type: ignore[no-redef]
        """Dummy class for running this on a non-Pi machine."""

        def __init__(
            self,
            channel: int = 1,
            wet_point: float | None = None,
            dry_point: float | None = None,
        ) -> None:
            self.channel = channel
            self._wet_point = wet_point or 10.0
            self._dry_point = dry_point or 0.0

        def set_wet_point(self, value: float) -> None:
            """Set the wet point for the dummy sensor."""
            self._wet_point = value

        def set_dry_point(self, value: float) -> None:
            """Set the dry point for the dummy sensor."""
            self._dry_point = value

        @property
        def moisture(self) -> int:
            """Return moisture level.

            Returns:
                int: random integer for fake moisture reading.
            """
            return randint(0, 900)

        @property
        def range(self) -> float:
            """Return the range sensor range (wet - dry points)."""
            return self._wet_point - self._dry_point

        @property
        def saturation(self) -> float:
            """Return saturation level.

            Returns:
                float: random float for fake saturation reading.
            """
            return round(randint(0, 10000) / 100, 2)

    class Pump:  # type: ignore[no-redef]
        """Dummy class for running this on a non-Pi machine."""

        def __init__(self, *_: None, **__: None) -> None:
            pass

        def dose(
            self,
            speed: float,
            timeout: float = 0.1,
            blocking: bool = True,
            force: bool = False,
        ) -> None:
            """Pulse the pump for timeout seconds.

            Args:
                speed (float): the pump speed
                timeout (float): timeout, in seconds, of the pump pulse
                blocking (bool): if true, function will block until pump has stopped
                force (bool): applies only to non-blocking. If true, any previous dose
                 will be replaced
            """

        def stop(self) -> None:
            """Stop the pump."""


PLANT_NAMES = (
    "Monstera",
    "Pineapple",
    "Ficus",
)


class Plant:
    """Class for monitoring (and watering, soon) plants.

    Args:
        name (str): the name of the plant
        sensor_number (int): the channel the sensor is plugged into on the hat
        pump_number (int): the channel the pump is plugged into on the hat
        wet_point (float): the moisture value at which the soil is considered wet
        dry_point (float): the moisture value at which the soil is considered dry
        get_limits_from_env_vars (bool): for getting initial point values from
         environment variables
    """

    SENSOR_ATTRIBUTES = ("moisture", "saturation")

    @on_exception()  # type: ignore[misc]
    def __init__(
        self,
        *,
        name: str,
        sensor_number: int,
        pump_number: int,
        wet_point: float | None = None,
        dry_point: float | None = None,
        get_limits_from_env_vars: bool = True,
    ) -> None:
        self.name = name

        self.water_mqtt_topic = f"/plant_monitor/{name.lower()}/water"

        self.moisture_sensor = Moisture(
            sensor_number, wet_point=wet_point, dry_point=dry_point
        )

        self._pump_number = pump_number
        self._pump = None

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

    @on_exception()  # type: ignore[misc]
    def get_limits_from_env_vars(self) -> None:
        """Get the wet/dry point limits from the environment."""

        if (
            wet_point := try_float(
                getenv(wet_point_ev_name := f"{self.name.upper()}_WET_POINT"), None
            )
        ) is None:
            LOGGER.error(
                "Unable to get env var %s: value is %s", wet_point_ev_name, wet_point
            )
        else:
            LOGGER.debug("Setting %s wet point to %s", self.name, wet_point)
            self.moisture_sensor.set_wet_point(wet_point)

        if (
            dry_point := try_float(
                getenv(dry_point_ev_name := f"{self.name.upper()}_DRY_POINT"), None
            )
        ) is None:
            LOGGER.error(
                "Unable to get env var %s: value is %s", dry_point_ev_name, dry_point
            )
        else:
            LOGGER.debug("Setting %s dry point to %s", self.name, dry_point)
            self.moisture_sensor.set_dry_point(dry_point)

    @on_exception()  # type: ignore[misc]
    def water(self, seconds: float) -> None:
        """Water the plant for X seconds.

        Args:
            seconds (float): how long to water the plant for
        """
        self.pump.dose(
            speed=1,
            timeout=seconds,
        )

        LOGGER.info("Watering for %f seconds", seconds)

    @property
    def home_assistant_payload(self) -> str:
        """Return a payload for Home Assistant.

        Returns:
            str: a payload for Home Assistant with the relevant readings.
        """
        return dumps(
            {
                attr_name: getattr(self, attr_name)
                for attr_name in self.SENSOR_ATTRIBUTES
            }
        )

    @property
    def moisture(self) -> float:
        """Return the raw moisture level.

        The value returned is the pulses/sec read from the soil moisture sensor.

        Returns:
            Union[str, float]: the moisture level, or a default if it's unknown
        """
        return float(round(self.moisture_sensor.moisture, 6))

    @property
    def pump(self) -> Pump:
        """The plant's water pump.

        This isn't an attribute, as only the waterer service needs the pump and
        creating a Pump instance within the monitor service will block the GPIO
        PWM usage.

        Returns:
            Pump: the plant's pump
        """
        if not self._pump:
            LOGGER.debug(
                "Creating pump for %s on channel %i", self.name, self._pump_number
            )
            self._pump = Pump(self._pump_number)

        return self._pump

    @property
    def saturation(self) -> str | float:
        """Calculate the saturation value from scratch.

        The `Moisture.saturation` is already rounded to 3dp (which then becomes
        1dp when we multiply it up to a percentage value).

        Returns:
            Union[str, float]: the saturation level, or a default if it's unknown
        """
        saturation: float = (
            # pylint: disable=protected-access
            float(self.moisture_sensor.moisture - self.moisture_sensor._dry_point)
        ) / self.moisture_sensor.range

        saturation = max(0.0, min(1.0, saturation))

        return round(saturation * 100, 3)

    def __str__(self) -> str:
        """Return a string representation of the plant."""
        return f"{self.name}:\t{self.moisture}"
