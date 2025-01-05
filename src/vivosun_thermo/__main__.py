import asyncio
import sys

from vivosun_thermo.app import VivosunThermoApp


def main():
    app = VivosunThermoApp()
    asyncio.run(app.run(sys.argv))


if __name__ == "__main__":
    main()
