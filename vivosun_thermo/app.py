import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Literal, NamedTuple

from vivosun_thermo.client import (
    PROBE_EXTERNAL,
    PROBE_MAIN,
    UNIT_CELSIUS,
    UNIT_FAHRENHEIT,
    ProbeType,
    TempUnit,
    VivosunThermoClient,
)
from vivosun_thermo.format import format_humidity, format_temperature, format_vpd
from vivosun_thermo.scanner import VivosunThermoScanner

FORMAT_TEXT = "text"
FORMAT_JSON = "json"


class GlobalCommandArgs(NamedTuple):
    adapter: str | None
    format: Literal["text", "json"]


class ListCommandArgs(GlobalCommandArgs):
    scan_timeout: float


class StatusCommandArgs(GlobalCommandArgs):
    connect_timeout: float
    read_timeout: float
    address: str
    unit: TempUnit


class VivosunThermoApp:
    async def run(self, argv: list[str]):
        parser = ArgumentParser(
            description="Vivosun Thermo command line interface",
            formatter_class=ArgumentDefaultsHelpFormatter,
            prog="vivosun-thermo",
        )

        parser.add_argument(
            "--adapter",
            help="bluetooth adapter name (hci0 on Linux)",
        )
        parser.add_argument(
            "-f",
            "--format",
            choices=(FORMAT_TEXT, FORMAT_JSON),
            help="output format",
            default=FORMAT_TEXT,
        )

        subparsers = parser.add_subparsers(required=True, help="sub-command help")

        parser_list = subparsers.add_parser(
            "list",
            help="scan for devices available nearby",
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        parser_list.add_argument(
            "--scan-timeout",
            type=float,
            help="scan timeout",
            default=30,
        )
        parser_list.set_defaults(func=self.cmd_list)

        parser_status = subparsers.add_parser(
            "status",
            help="read status (temperature, humidity, vpd)",
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        parser_status.add_argument(
            "-u",
            "--unit",
            choices=(UNIT_CELSIUS, UNIT_FAHRENHEIT),
            help="temperature unit",
            default=UNIT_CELSIUS,
        )
        parser_status.add_argument(
            "--connect-timeout",
            type=float,
            help="connect timeout",
            default=15,
        )
        parser_status.add_argument(
            "--read-timeout",
            type=float,
            help="read timeout",
            default=0.5,
        )
        parser_status.add_argument(
            "address",
            help="device address",
        )
        parser_status.set_defaults(func=self.cmd_status)

        args = parser.parse_args(argv[1:])

        await args.func(args)

    async def cmd_list(self, args: ListCommandArgs):
        if args.format == FORMAT_JSON:
            result = [
                ({"address": dev.address, "name": dev.name})
                async for dev in self._list_devices(args)
            ]
            self._print_json(result)
        else:
            async for dev in self._list_devices(args):
                print(f"{dev.address} {dev.name}")

    async def _list_devices(self, args: ListCommandArgs):
        for dev in await VivosunThermoScanner.discover(
            timeout=args.scan_timeout,
            adapter=args.adapter,
        ):
            yield dev

    async def cmd_status(self, args: StatusCommandArgs):
        async with VivosunThermoClient(
            args.address,
            adapter=args.adapter,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
        ) as client:
            if args.format == FORMAT_JSON:
                await self._print_status_json(client, args.unit)
            else:
                await self._print_status_text(client, args.unit)

    async def _print_status_json(self, client: VivosunThermoClient, unit: TempUnit):
        main_sensor = await self._get_probe_obj(client, PROBE_MAIN, unit)
        external_sensor = await self._get_probe_obj(client, PROBE_EXTERNAL, unit)
        result = {
            "main_sensor": main_sensor,
            **({"external_sensor": external_sensor} if external_sensor is not None else {}),
        }
        self._print_json(result)

    async def _get_probe_obj(self, client: VivosunThermoClient, probe: ProbeType, unit: TempUnit):
        if probe == PROBE_EXTERNAL and not await client.has_external_probe():
            return None
        return {
            "temperature": await client.current_temperature(probe, unit),
            "humidity": await client.current_humidity(probe),
            "vpd": await client.current_vpd(probe),
        }

    async def _print_status_text(self, client: VivosunThermoClient, unit: TempUnit):
        await self._print_probe_text(client, PROBE_MAIN, unit)
        if await client.has_external_probe():
            print("")
            await self._print_probe_text(client, PROBE_EXTERNAL, unit)

    async def _print_probe_text(
        self, client: VivosunThermoClient, probe: ProbeType, unit: TempUnit
    ):
        temp = await client.current_temperature(probe, unit)
        humidity = await client.current_humidity(probe)
        vpd = await client.current_vpd(probe)

        print(f"{"Main" if probe == PROBE_MAIN else "External"} Sensor:")
        print(f"  Temperature: {format_temperature(temp, unit)}")
        print(f"  Humidity: {format_humidity(humidity)}")
        print(f"  VPD: {format_vpd(vpd)}")

    def _print_json(self, obj: object):
        print(json.dumps(obj, indent=4))
