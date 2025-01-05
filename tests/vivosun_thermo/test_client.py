import asyncio
from typing import Any
from unittest import mock
from unittest.mock import MagicMock

import pytest
from bleak import BleakClient

from vivosun_thermo.client import (
    CHAR_STATUS,
    COMMAND_0D,
    PROBE_EXTERNAL,
    PROBE_MAIN,
    UNIT_CELSIUS,
    UNIT_FAHRENHEIT,
    VivosunThermoClient,
)


class TestVivosunThermoClient:
    msg_0d_int = bytearray.fromhex("0D 4B 01 C3 02 88 00 FF  FF FF FF FF FF 00 00 00  00 00 00 00")
    msg_0d_both = bytearray.fromhex("0D 56 01 7D 02 99 00 5A  01 6E 02 9E 00 00 00 00  00 00 00 00")

    @pytest.fixture
    def bleak_client(self):
        notify_callback: Any = None

        def start_notify_side_effect(char: Any, callback: Any):
            nonlocal notify_callback
            if char == CHAR_STATUS:
                notify_callback = callback
            else:
                raise ValueError(f"Unknown characteristic {char}")

        def stop_notify_side_effect(char: Any):
            nonlocal notify_callback
            if char == CHAR_STATUS:
                notify_callback = None
            else:
                raise ValueError(f"Unknown characteristic {char}")

        def write_gatt_char_side_effect(char: Any, data: bytearray):
            loop = asyncio.get_running_loop()

            if notify_callback is not None:
                if data.startswith(COMMAND_0D):
                    loop.call_soon(lambda buf: notify_callback(char, buf), self.msg_0d_int)
                else:
                    raise ValueError(f"Unknown command {data}")
            else:
                raise ValueError(f"Notify not started for characteristic {char}")

        client = MagicMock(BleakClient)

        client.start_notify.side_effect = start_notify_side_effect
        client.write_gatt_char.side_effect = write_gatt_char_side_effect
        client.stop_notify.side_effect = stop_notify_side_effect

        with mock.patch("vivosun_thermo.client.BleakClient") as MockBleakClient:
            MockBleakClient.return_value = client
            yield client

    @pytest.fixture
    def client(self, bleak_client):
        return VivosunThermoClient("mock_address")

    @pytest.mark.asyncio
    async def test_connect(self, client, bleak_client):
        await client.connect()
        bleak_client.connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, client, bleak_client):
        await client.disconnect()
        bleak_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    def test_is_connected_true(self, client, bleak_client):
        bleak_client.is_connected = True
        assert client.is_connected is True

    @pytest.mark.asyncio
    def test_is_connected_false(self, client, bleak_client):
        bleak_client.is_connected = False
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_current_temperature_main_c(self, client):
        value = await client.current_temperature(probe=PROBE_MAIN, unit=UNIT_CELSIUS)
        assert round(value, 1) == 20.7

    @pytest.mark.asyncio
    async def test_current_temperature_main_f(self, client):
        value = await client.current_temperature(probe=PROBE_MAIN, unit=UNIT_FAHRENHEIT)
        assert round(value, 1) == 69.2

    @pytest.mark.asyncio
    async def test_current_temperature_ext_c(self, client):
        self.msg_0d_int = self.msg_0d_both
        value = await client.current_temperature(probe=PROBE_EXTERNAL, unit=UNIT_CELSIUS)
        assert round(value, 1) == 21.6

    @pytest.mark.asyncio
    async def test_current_temperature_ext_f(self, client):
        self.msg_0d_int = self.msg_0d_both
        value = await client.current_temperature(probe=PROBE_EXTERNAL, unit=UNIT_FAHRENHEIT)
        assert round(value, 1) == 70.9

    @pytest.mark.asyncio
    async def test_current_humidity_main(self, client):
        value = await client.current_humidity(probe=PROBE_MAIN)
        assert round(value) == 44

    @pytest.mark.asyncio
    async def test_current_humidity_external(self, client):
        self.msg_0d_int = self.msg_0d_both
        value = await client.current_humidity(probe=PROBE_EXTERNAL)
        assert round(value) == 39

    @pytest.mark.asyncio
    async def test_current_vpd_main(self, client):
        value = await client.current_vpd(probe=PROBE_MAIN)
        assert round(value, 2) == 1.36

    @pytest.mark.asyncio
    async def test_current_vpd_external(self, client):
        self.msg_0d_int = self.msg_0d_both
        value = await client.current_vpd(probe=PROBE_EXTERNAL)
        assert round(value, 2) == 1.58

    @pytest.mark.asyncio
    async def test_has_external_probe_true(self, client):
        self.msg_0d_int = self.msg_0d_both
        value = await client.has_external_probe()
        assert value is True

    @pytest.mark.asyncio
    async def test_has_external_probe_false(self, client):
        value = await client.has_external_probe()
        assert value is False
