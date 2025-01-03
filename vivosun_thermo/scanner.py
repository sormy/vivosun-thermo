from bleak import BleakScanner
from bleak.backends.device import BLEDevice

NAME_VS_THB1S = "ThermoBeacon2"


class VivosunThermoScanner:
    @classmethod
    async def discover(cls, timeout: float = 30, adapter: str | None = None) -> list[BLEDevice]:
        devices = await BleakScanner.discover(timeout=timeout, adapter=adapter)
        return [dev for dev in devices if dev.name == NAME_VS_THB1S]
