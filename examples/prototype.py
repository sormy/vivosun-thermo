import asyncio
import csv
import math
import struct
from datetime import datetime, timezone

import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from hexdump import hexdump

UUID_COMMAND = "0000fff5-0000-1000-8000-00805f9b34fb"
UUID_STATUS = "0000fff3-0000-1000-8000-00805f9b34fb"

COMMAND_1000 = bytearray([0x10, 0x00])
COMMAND_25 = bytearray([0x25])
COMMAND_1100 = bytearray([0x11, 0x00])
COMMAND_1101 = bytearray([0x11, 0x01])
COMMAND_0D = bytearray([0x0D])

SAVE_DUMPS = False


class AsyncHeartbeat:
    def __init__(self, timeout: float = 0.5):
        self.timeout = timeout
        self._sleep_timeout = 0.1
        self._future = asyncio.get_event_loop().create_future()
        self._task = asyncio.create_task(self._watch_timeout())
        self._last_alive = asyncio.get_event_loop().time()

    async def _watch_timeout(self):
        while True:
            if self._future.done():
                return
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_alive
            remaining = self.timeout - elapsed
            if remaining <= 0:
                if not self._future.done():
                    self._future.set_result("Timed out")
                return
            await asyncio.sleep(min(remaining, self._sleep_timeout))

    def alive(self):
        self._last_alive = asyncio.get_event_loop().time()

    def future(self):
        return self._future

    def cancel(self):
        if not self._future.done():
            self._future.set_result("Canceled")


def calculate_vpd(temperature_c: float, humidity: float) -> float:
    e_s = 0.6108 * math.exp((17.27 * temperature_c) / (temperature_c + 237.3))
    e_a = e_s * (humidity / 100)
    return e_s - e_a


def pad_bytearray(data: bytearray, size: int) -> bytearray:
    if len(data) > size:
        raise ValueError(f"Input exceeds {size} bytes")
    return data + bytearray(size - len(data))


async def read_single_value(
    client: BleakClient, command: bytearray, timeout: float = 1.0
) -> bytearray:
    result = bytearray()
    heartbeat = AsyncHeartbeat(timeout)

    def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
        result.extend(data)
        heartbeat.cancel()  # do not wait for more packets

    await client.start_notify(UUID_STATUS, callback)
    await client.write_gatt_char(UUID_COMMAND, command)
    await heartbeat.future()
    await client.stop_notify(UUID_STATUS)
    heartbeat.cancel()
    return result


async def read_multi_value(
    client: BleakClient, command: bytearray, timeout: float = 1.0
) -> list[bytearray]:
    result: list[bytearray] = list()
    heartbeat = AsyncHeartbeat(timeout)

    def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
        heartbeat.alive()
        result.append(data)

    await client.start_notify(UUID_STATUS, callback)
    await client.write_gatt_char(UUID_COMMAND, command)
    await heartbeat.future()
    await client.stop_notify(UUID_STATUS)
    heartbeat.cancel()
    return result


async def describe_device(client: BleakClient):
    for service in client.services:
        print(f"Service UUID: {service.uuid}")
        for char in service.characteristics:
            print(f"    Characteristic UUID: {char.uuid}")
            print(f"      Properties: {char.properties}")

            if "read" in char.properties:
                value = "N/A"
                try:
                    value = await client.read_gatt_char(char.uuid)
                    value = value.decode("utf-8")
                except Exception:
                    pass
                print(f"      Value: {value}")


async def exec_command(client: BleakClient, command: bytearray, single: bool = False):
    print(f"Running command: {command.hex()}")
    if single:
        data = await read_single_value(client, bytearray(command))
    else:
        data = await read_multi_value(client, bytearray(command))
        data = bytearray(b"".join([pad_bytearray(record, 32) for record in data]))
    hexdump(data)
    if SAVE_DUMPS:
        with open(f"dump_{command.hex()}.bin", "wb") as file:
            file.write(data)
    return data


def plot_save(values: list, filename: str):
    plt.plot(values, marker="o")
    plt.xlabel("Index")
    plt.ylabel("Value")
    plt.grid(True)
    plt.savefig(filename)
    plt.close()


def csv_values(file_path: str, col_index: int):
    values: list[float] = []
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            values.append(float(row[col_index]))
    return values


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) / (9 / 5)


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32


def decode_float(raw: int):
    return 1 / 16 * raw


async def test_1100(client: BleakClient):
    # bytearray([0x11, 0x00, 0x00, 0x00, 0x00, 0x00])
    data = await exec_command(client, COMMAND_1100)
    await client.disconnect()

    values = [struct.unpack_from("<h", data, i)[0] for i in range(2, len(data), 32)]
    plot_save(values, "figure_bn.png")
    print(f"raw n: max={max(values)}, min={min(values)}")

    values = [struct.unpack_from("<h", data, i)[0] for i in range(4, len(data), 32)]
    plot_save(values, "figure_btr.png")
    print(f"raw tr: max={max(values)}, min={min(values)}")
    values_d = [decode_float(v) for v in values]
    print(f"raw tdc: max={max(values_d)}, min={min(values_d)}")
    plot_save(values_d, "figure_btc.png")

    last_temp = values_d[-1]

    values = [struct.unpack_from("<h", data, i)[0] for i in range(6, len(data), 32)]
    plot_save(values, "figure_bhr.png")
    print(f"raw hr: max={max(values)}, min={min(values)}")
    values_d = [decode_float(v) for v in values]
    print(f"raw hd: max={max(values_d)}, min={min(values_d)}")
    plot_save(values_d, "figure_bhd.png")

    last_humidity = values_d[-1]

    # values = [struct.unpack_from("<h", data, i)[0] for i in range(4, len(data), 32)]
    # plot_save(values, "figure1a.png")

    # values = [struct.unpack_from("<l", data, i)[0] for i in range(2, len(data), 32)]
    # dates = [datetime.fromtimestamp(value, tz=timezone.utc).isoformat() for value in values]
    # print(dates)

    print(f"last temp = {last_temp}C")
    print(f"last humidity = {last_humidity}%")
    print(f"last vpd = {calculate_vpd(last_temp, last_humidity)}%")

    vivosun_file = "AeroLab Thermo-Hygrometer_export_202501011709.csv"

    values = csv_values(vivosun_file, 1)
    plot_save(values, "figure_atf.png")
    print(f"app tf: max={max(values)}, min={min(values)}")

    values_c = [fahrenheit_to_celsius(v) for v in values]
    plot_save(values_c, "figure_atc.png")
    print(f"app tc: max={max(values_c)}, min={min(values_c)}")

    values = csv_values(vivosun_file, 2)
    plot_save(values, "figure_ah.png")
    print(f"app h: max={max(values)}, min={min(values)}")

    values = csv_values(vivosun_file, 3)
    plot_save(values, "figure_av.png")
    print(f"app v: max={max(values)}, min={min(values)}")


async def test_device(device_address: str):
    print(f"Connecting to {device_address}...")

    async with BleakClient(device_address, timeout=15) as client:
        # await describe_device(client)
        await exec_command(client, COMMAND_1000, True)
        await exec_command(client, COMMAND_25, True)
        await exec_command(client, COMMAND_1100)
        await exec_command(client, COMMAND_1101)
        # test_1100

        data = await exec_command(client, COMMAND_0D, True)
        main_temp = decode_float(struct.unpack_from("<h", data, 1)[0])
        main_hum = decode_float(struct.unpack_from("<h", data, 3)[0])
        main_vpd = calculate_vpd(main_temp, main_hum)
        probe_temp = decode_float(struct.unpack_from("<h", data, 7)[0])
        probe_hum = decode_float(struct.unpack_from("<h", data, 9)[0])
        probe_vpd = calculate_vpd(probe_temp, probe_hum)
        print(f"main temp = {round(main_temp, 1):.1f}°C")
        print(f"main hum = {round(main_hum, 0):.0f}%")
        print(f"main vpd = {round(main_vpd, 2):.2f}kPa")
        print(f"probe temp = {round(probe_temp, 1):.1f}°C")
        print(f"probe hum = {round(probe_hum, 0):.0f}%")
        print(f"probe vpd = {round(probe_vpd, 2):.2f}kPa")


async def test_devices():
    devices = await BleakScanner.discover(timeout=30)
    for device in devices:
        if device.name == "ThermoBeacon2":
            print(f"Found device {device.name} [{device.address}]")
            await test_device(device.address)


async def test():
    # await test_devices()
    await test_device("5648A2C2-E0A3-6E85-000C-30D6C1C1FBCD")


def main():
    asyncio.run(test())


main()
