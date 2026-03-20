"""MinuteMap sensor platform.

Each sensor resolves its current value from a YearMinuteMap spec,
polled once per minute aligned to the top of the minute.

Example configuration:

    sensor:
      - platform: minutemap
        sensors:
          living_room_brightness:
            unit_of_measurement: "%"
            spec:
              "*": 50
              "h6-9": 80
              "h19-23": 30
          heating_setpoint:
            unit_of_measurement: "°C"
            spec:
              "*": 18
              "h6-8": 21
              "h17-22": 21
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
import voluptuous as vol
from typing import Callable
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
#  from minutemap import YearMinuteMap
from .lib.minutemap import YearMinuteMap
from .const import CONF_SENSORS, CONF_SPEC, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Per-sensor schema
SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Required(CONF_SPEC): dict,
    }
)

# Platform schema: a dict of sensor_name -> sensor config
PLATFORM_SCHEMA_BASE = vol.Schema(
    {
        vol.Required(CONF_SENSORS): vol.Schema({cv.slug: SENSOR_SCHEMA}),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up MinuteMap sensors from YAML configuration."""
    if YearMinuteMap is None:
        _LOGGER.error(
            "minutemap package is not installed. "
            "Add 'minutemap' to your requirements or reinstall the integration."
        )
        return

    sensors_config: dict = config[CONF_SENSORS]
    entities = []

    for sensor_id, sensor_cfg in sensors_config.items():
        spec = sensor_cfg[CONF_SPEC]
        unit = sensor_cfg.get(CONF_UNIT_OF_MEASUREMENT)
        name = sensor_id.replace("_", " ").title()

        try:
            ymm = YearMinuteMap(spec)
        except ValueError as exc:
            _LOGGER.error("Invalid spec for sensor '%s': %s", sensor_id, exc)
            continue

        entities.append(MinuteMapSensor(hass, sensor_id, name, unit, ymm))

    async_add_entities(entities)


def _next_whole_minute() -> datetime:
    """Return the next whole minute in local time."""
    now = dt_util.now()
    return (now + timedelta(minutes=1)).replace(second=0, microsecond=0)


class MinuteMapSensor(SensorEntity):
    """A sensor whose state is resolved from a YearMinuteMap each minute."""

    _attr_should_poll = False   # We drive updates ourselves via time tracking

    def __init__(
        self,
        hass: HomeAssistant,
        sensor_id: str,
        name: str,
        unit: str | None,
        ymm: YearMinuteMap,
    ) -> None:
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._ymm = ymm
        self._attr_native_value = None
        self._unsub_timer: Callable | None = None

    async def async_added_to_hass(self) -> None:
        """Start the per-minute update cycle when entity is added."""
        self._update_value()
        self._schedule_next_update()

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the timer when entity is removed."""
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _schedule_next_update(self) -> None:
        """Schedule the next update at the top of the next minute."""
        self._unsub_timer = async_track_point_in_time(
            self.hass,
            self._handle_timer,
            _next_whole_minute(),
        )

    @callback
    def _handle_timer(self, now: datetime) -> None:
        """Called at the top of each minute."""
        self._update_value()
        self._schedule_next_update()

    def _update_value(self) -> None:
        """Resolve and apply the current value from the YearMinuteMap."""
        now = dt_util.now().replace(second=0, microsecond=0)
        value = self._ymm.get_value(now)

        if value is None:
            self._attr_native_value = None
            self._attr_available = True   # entity is alive, just no matching spec
            # STATE_UNKNOWN is returned automatically when native_value is None
        else:
            self._attr_native_value = value
            self._attr_available = True

        self.async_write_ha_state()
