import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Literal, NamedTuple

from vivosun_thermo.client import (
    PROBE_EXTERNAL,
    PROBE_MAIN,
    ProbeType,
    TempUnit,
    VivosunThermoClient,
)
from vivosun_thermo.format import format_humidity, format_temperature, format_vpd
from vivosun_thermo.scanner import VivosunThermoScanner


class ListCommandArgs(NamedTuple):
    adapter: str | None
    scan_timeout: int


class StatusCommandArgs(NamedTuple):
    adapter: str | None
    connect_timeout: int
    read_timeout: int
    address: str
    unit: Literal["c", "f"]
    format: Literal["text", "json"]


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
        parser_list.set_defaults(func=self.list)

        parser_status = subparsers.add_parser(
            "status",
            help="read status (temperature, humidity, vpd)",
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        parser_status.add_argument(
            "-u",
            "--unit",
            choices=("c", "f"),
            help="temperature unit",
            default="c",
        )
        parser_status.add_argument(
            "-f",
            "--format",
            choices=("text", "json"),
            help="output format",
            default="text",
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
        parser_status.set_defaults(func=self.status)

        args = parser.parse_args(argv[1:])

        await args.func(args)

    async def list(self, args: ListCommandArgs):
        for dev in await VivosunThermoScanner.discover(
            timeout=args.scan_timeout,
            adapter=args.adapter,
        ):
            print(f"{dev.address}\t{dev.name}")

    async def status(self, args: StatusCommandArgs):
        async with VivosunThermoClient(
            args.address,
            adapter=args.adapter,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
        ) as client:
            if args.format == "json":
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
        print(json.dumps(result, indent=4))

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
