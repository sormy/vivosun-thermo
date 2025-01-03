# Vivosun Thermo Python Library and CLI

Vivosun Thermo is a Python library and CLI tool for interacting with Vivosun Thermo devices via
Bluetooth. It allows you to:

-   Read the current temperature, humidity, and computed VPD from your device.
-   Scan for nearby devices.
-   Use a simple API for custom integrations.

The library supports both a command-line interface (CLI) and a Python API. It is licensed under the
MIT License.

## Features

-   **CLI**: Command-line interface to scan and read data from Vivosun Thermo devices.
-   **API**: A Python interface for programmatic access to temperature, humidity, and VPD readings.
-   **Flexible Output**: Supports text and JSON output formats for integration with other tools.

## Supported Devices

-   **VS-THB1S**: VIVOSUN AeroLab Hygrometer Thermometer

## Installation

```sh
brew install pipx
pipx install vivosun_thermo
```

## CLI Usage

### Scan for Nearby Devices

Use the `list` command to scan for nearby devices:

```sh
vivosun-thermo list
```

Options:

-   `-f`, `--format`: Output format (text or json). Default: text.
-   `--scan-timeout`: Duration (in seconds) for scanning devices.
-   `--adapter`: Bluetooth adapter name (e.g., hci0 on Linux).

NOTE: Already connected devices won't show up in the list.

### Read Status from a Device

Use the `status` command to read temperature, humidity, and VPD:

```sh
vivosun-thermo status <device_address>
```

Options:

-   `-u`, `--unit`: Temperature unit (c for Celsius, f for Fahrenheit). Default: c.
-   `-f`, `--format`: Output format (text or json). Default: text.
-   `--connect-timeout`: Timeout for connecting to the device. Default: 15 seconds.
-   `--read-timeout`: Timeout for reading data. Default: 0.5 seconds.
-   `--adapter`: Bluetooth adapter name (e.g., hci0 on Linux).

NOTE: Enable pairing mode on device for initial connection.

## Python API Usage

Example:

```python
import asyncio
from vivosun_thermo import VivosunThermoClient, PROBE_MAIN, UNIT_CELSIUS

async def main():
    async with VivosunThermoClient("device_address") as client:
        temperature = await client.current_temperature(PROBE_MAIN, UNIT_CELSIUS)
        humidity = await client.current_humidity(PROBE_MAIN)
        vpd = await client.current_vpd(PROBE_MAIN)
        print(f"Temperature: {temperature}°C")
        print(f"Humidity: {humidity}%")
        print(f"VPD: {vpd} kPa")

asyncio.run(main())
```

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
