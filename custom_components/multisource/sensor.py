"""Support for displaying numeric (float) value coming from multiple seensors (sources)"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
)

from homeassistant.const import (
    CONF_TYPE,
    CONF_SENSORS,
    CONF_FORCE_UPDATE,
    CONF_ICON,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change

_LOGGER = logging.getLogger(__name__)

DEFAULT_FORCE_UPDATE = False

CONF_ROUND_DIGITS = "round_digits"
DEFAULT_ROUND_DIGITS = -1 # -1 means don't round at all!

CONF_SOURCES = "sources"
CONF_SELECTABLE_SOURCES = "selectable_sources"
DEFAULT_SELECTABLE_SOURCES = False # cannot disable sources

CONF_SELECTORS = "selectors"


ATTR_MIN = "min"
ATTR_LAST = "last"

SENSOR_TYPES = {
    ATTR_MIN: "min",
    ATTR_LAST: "last",
}


SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TYPE, default=SENSOR_TYPES[ATTR_LAST]): vol.All(
            cv.string, vol.In(SENSOR_TYPES.values())
        ),
        vol.Required(CONF_SOURCES): cv.entity_ids,
        vol.Optional(CONF_SELECTORS): cv.entity_ids,
        vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
        vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
        vol.Optional(CONF_ROUND_DIGITS, default=DEFAULT_ROUND_DIGITS): vol.Coerce(int),
        vol.Optional(CONF_SELECTABLE_SOURCES, default=DEFAULT_SELECTABLE_SOURCES): cv.boolean,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SENSORS): cv.schema_with_slug_keys(SENSOR_SCHEMA)}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up sensors."""
    sensors = []

    for device, device_config in config[CONF_SENSORS].items():
        sensor_type = device_config.get(CONF_TYPE)
        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        sources = device_config.get(CONF_SOURCES)
        round_digits = device_config.get(CONF_ROUND_DIGITS)
        selectable_sources = device_config.get(CONF_SELECTABLE_SOURCES)

        sensors.append(
            MultiSourceSensor(
                hass,
                device,
                sensor_type,
                friendly_name,
                sources,
                selectable_sources,
                round_digits,
                device_config
            )
        )

    async_add_entities(sensors)

    return True

def calc_min(sensor_values):
    """Calculate min value, honoring unknown states."""
    val = None
    for sval in sensor_values:
        if sval != STATE_UNKNOWN:
            if val is None or val > sval:
                val = sval
    return val

def create_selectors(sources):
    """Create a default list of default selectors (input_booleans)"""
    selectors = []
    for source in sources:
        part = source.split('.', 1)
        assert len(part) == 2, "invalid source %s" % source
        selectors.append( "input_boolean.{}_selected".format(part[1]) )
    return selectors


class MultiSourceSensor(Entity):
    """Representation of a multisource sensor."""

    def __init__(self, hass, device_id, sensor_type, friendly_name, sources, selectable_sources, round_digits, config):
        """Initialize the multisource sensor."""
        # inherited properties
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, device_id, hass=hass
        )

        # new properties
        self._config = config
        self._name = friendly_name

        self._sensor_type = sensor_type
        self._sources = sources

        self._selectable_sources = selectable_sources
        if selectable_sources:
            self._selectors = config.get(CONF_SELECTORS, create_selectors(sources))

        self._round_digits = round_digits

        self._unit_of_measurement = None
        self._unit_of_measurement_mismatch = False
        self._icon = None
        self.states = {}
        self.min = self.last = None

        def not_selected(entity_id):
            """Return state of the appropriate selector"""
            #if not self._selectable_sources:
            #    return False

            try:
                index = self._sources.index(entity_id)
                selector_id = self._selectors[index]
                return self.hass.states.is_state(selector_id, 'off')
            except ValueError:
                _LOGGER.warning(
                    "not_selected: error processing %s", entity_id
                )

            return True

        @callback
        def async_multisource_sensor_selector_listener(selector_id, old_state, new_state):
            """Handle the selectors state changes."""
            if new_state.state:
                try:
                    index = self._selectors.index(selector_id)
                    source_id = self._sources[index]
                    source_state = STATE_UNKNOWN
                    if new_state.state == 'on':
                        source_obj = self.hass.states.get(source_id)
                        # on HA start state can be unknown etc - that's pretty normal
                        if source_obj and source_obj.state not in [None, STATE_UNKNOWN, STATE_UNAVAILABLE]:
                            source_state = float(source_obj.state)

                    self.states[source_id] = source_state
                    self.hass.async_add_job(self.async_update_ha_state, True)
                except ValueError:
                    _LOGGER.warning(
                        "selector_listener: error processing %s", selector_id
                    )

        @callback
        def async_multisource_sensor_state_listener(entity, old_state, new_state):
            """Handle the sensors state changes."""
            if self._unit_of_measurement is None:
                self._unit_of_measurement = new_state.attributes.get(
                    ATTR_UNIT_OF_MEASUREMENT
                )

            if self._unit_of_measurement != new_state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT
            ):
                _LOGGER.warning(
                    "Units of measurement do not match for entity %s", self.entity_id
                )
                self._unit_of_measurement_mismatch = True

            if self._icon is None:
                self._icon = new_state.attributes.get(
                    CONF_ICON
                )

            if new_state.state is None or new_state.state in [
                    STATE_UNKNOWN,
                    STATE_UNAVAILABLE,
                ] or (self._selectable_sources and not_selected(entity)):
                self.states[entity] = STATE_UNKNOWN
                self.hass.async_add_job(self.async_update_ha_state, True)
                return

            try:
                self.states[entity] = self.last = float(new_state.state)
            except ValueError:
                _LOGGER.warning(
                    "Unable to store state. " "Only numerical states are supported"
                )

            self.hass.async_add_job(self.async_update_ha_state, True)

        async_track_state_change(
            self.hass, self._sources, async_multisource_sensor_state_listener
        )

        if selectable_sources:
            async_track_state_change(
                    self.hass, self._selectors, async_multisource_sensor_selector_listener
            )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._unit_of_measurement_mismatch:
            return None

        state = getattr(
            self, next(k for k, v in SENSOR_TYPES.items() if self._sensor_type == v)
        )

        # if it's unknown or they said don't round, just pass the state out
        if state is None or state == STATE_UNKNOWN or self._round_digits == DEFAULT_ROUND_DIGITS:
            return state
        # it's float, do some magic to return a nicely formatted number
        elif self._round_digits:
            return round(state, self._round_digits)
        else:
            return int(state)

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if self._unit_of_measurement_mismatch:
            return "ERR"
        else:
            return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def force_update(self):
        """Force update."""
        return self._config[CONF_FORCE_UPDATE]

    async def async_update(self):
        """Get the latest data and updates the states."""
        if self._sensor_type == ATTR_MIN:
            sensor_values = [self.states[k] for k in self._sources if k in self.states]
            self.min = calc_min(sensor_values)
        elif self._sensor_type == ATTR_LAST and all(state in [STATE_UNKNOWN, STATE_UNAVAILABLE] for state in self.states.values()):
            self.last = STATE_UNKNOWN
