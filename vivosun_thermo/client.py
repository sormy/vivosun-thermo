import asyncio
import struct
from typing import Literal

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice

from vivosun_thermo.conversion import calculate_vpd, celsius_to_fahrenheit

UUID_COMMAND = "0000fff5-0000-1000-8000-00805f9b34fb"
UUID_STATUS = "0000fff3-0000-1000-8000-00805f9b34fb"

COMMAND_0D = bytearray([0x0D])

OFFSET_0D_INT_TEMP = 1
OFFSET_0D_INT_HUMIDITY = 3
OFFSET_0D_EXT_TEMP = 7
OFFSET_0D_EXT_HUMIDITY = 9

VALUE_NONE = -1  # 0xFF

PROBE_MAIN = "main"
PROBE_EXTERNAL = "external"

UNIT_CELSIUS = "c"
UNIT_FAHRENHEIT = "f"

ProbeType = Literal["main", "external"]
TempUnit = Literal["c", "f"]


class VivosunThermoClient:
    def __init__(
        self,
        address_or_ble_device: BLEDevice | str,
        connect_timeout: float = 15,
        read_timeout: float = 0.5,
        cache_ttl: float = 0.5,
        adapter: str | None = None,
    ):
        self._client = BleakClient(address_or_ble_device, timout=connect_timeout, adapter=adapter)
        self._data_0d = bytearray()
        self._data_0d_ts = 0.0
        self.read_timeout = read_timeout
        self.cache_ttl = cache_ttl

    async def __aenter__(self):
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.disconnect()

    async def connect(self):
        await self._client.connect()

    async def disconnect(self):
        await self._client.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    async def current_temperature(
        self, probe: ProbeType = PROBE_MAIN, unit: TempUnit = UNIT_CELSIUS
    ) -> float:
        data = await self._read_status_0d()
        offset = OFFSET_0D_INT_TEMP if probe == PROBE_MAIN else OFFSET_0D_EXT_TEMP
        temp_c = self._decode_float(struct.unpack_from("<h", data, offset)[0])
        return temp_c if unit == UNIT_CELSIUS else celsius_to_fahrenheit(temp_c)

    async def current_humidity(self, probe: ProbeType = PROBE_MAIN) -> float:
        data = await self._read_status_0d()
        offset = OFFSET_0D_INT_HUMIDITY if probe == PROBE_MAIN else OFFSET_0D_EXT_HUMIDITY
        return self._decode_float(struct.unpack_from("<h", data, offset)[0])

    async def current_vpd(self, probe: ProbeType = PROBE_MAIN) -> float:
        temp_c = await self.current_temperature(probe, UNIT_CELSIUS)
        humidity = await self.current_humidity(probe)
        return calculate_vpd(temp_c, humidity)

    async def has_external_probe(self) -> bool:
        data = await self._read_status_0d()
        raw_probe_temp = struct.unpack_from("<h", data, OFFSET_0D_EXT_TEMP)[0]
        raw_probe_humidity = struct.unpack_from("<h", data, OFFSET_0D_EXT_HUMIDITY)[0]
        return raw_probe_temp != VALUE_NONE and raw_probe_humidity != VALUE_NONE

    def _decode_float(self, raw: int):
        return 1 / 16 * raw

    async def _read_status_0d(self) -> bytearray:
        now = asyncio.get_event_loop().time()
        if now - self._data_0d_ts >= self.cache_ttl:
            self._data_0d = await self._read_value(COMMAND_0D)
            self._data_0d_ts = now
        return self._data_0d

    async def _read_value(self, command: bytearray) -> bytearray:
        future = asyncio.get_event_loop().create_future()

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            future.set_result(data)

        await self._client.start_notify(UUID_STATUS, callback)
        await self._client.write_gatt_char(UUID_COMMAND, command)
        result = await asyncio.wait_for(future, self.read_timeout)
        await self._client.stop_notify(UUID_STATUS)
        return result
