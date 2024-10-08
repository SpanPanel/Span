"""Control switches."""

import logging
from functools import cached_property
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN, CircuitRelayState
from .coordinator import SpanPanelCoordinator
from .span_panel import SpanPanel
from .util import panel_to_device_info

ICON = "mdi:toggle-switch"

_LOGGER = logging.getLogger(__name__)


class SpanPanelCircuitsSwitch(CoordinatorEntity[SpanPanelCoordinator], SwitchEntity):
    """Represent a switch entity."""

    def __init__(self, coordinator: SpanPanelCoordinator, id: str, name: str) -> None:
        """Initialize the values."""
        _LOGGER.debug("CREATE SWITCH %s" % name)
        span_panel: SpanPanel = coordinator.data

        self.id = id
        self._attr_unique_id = f"span_{span_panel.status.serial_number}_relay_{id}"
        self._attr_device_info = panel_to_device_info(span_panel)
        super().__init__(coordinator)

    def turn_on(self, **kwargs: Any) -> None:
        """Synchronously turn the switch on."""
        self.hass.create_task(self.async_turn_on(**kwargs))

    def turn_off(self, **kwargs: Any) -> None:
        """Synchronously turn the switch off."""
        self.hass.create_task(self.async_turn_off(**kwargs))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        span_panel: SpanPanel = self.coordinator.data
        curr_circuit = span_panel.circuits[self.id]
        await span_panel.api.set_relay(curr_circuit, CircuitRelayState.CLOSED)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        span_panel: SpanPanel = self.coordinator.data
        curr_circuit = span_panel.circuits[self.id]
        await span_panel.api.set_relay(curr_circuit, CircuitRelayState.OPEN)
        await self.coordinator.async_request_refresh()

    @cached_property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    @cached_property
    def name(self):
        """Return the switch name."""
        span_panel: SpanPanel = self.coordinator.data
        return f"{span_panel.circuits[self.id].name} Breaker"

    @property
    def is_on(self) -> bool:
        """Get switch state."""
        span_panel: SpanPanel = self.coordinator.data
        return span_panel.circuits[self.id].is_relay_closed


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up envoy sensor platform.
    """

    _LOGGER.debug("ASYNC SETUP ENTRY SWITCH")
    data: dict[str, Any] = hass.data[DOMAIN][config_entry.entry_id]

    coordinator: SpanPanelCoordinator = data[COORDINATOR]
    span_panel: SpanPanel = coordinator.data

    entities: list[SpanPanelCircuitsSwitch] = []

    for circuit_id, circuit_data in span_panel.circuits.items():
        if circuit_data.is_user_controllable:
            entities.append(SpanPanelCircuitsSwitch(coordinator, circuit_id, circuit_data.name))

    async_add_entities(entities)
