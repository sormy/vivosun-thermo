import asyncio
import sys

from vivosun_thermo.app import VivosunThermoApp

if __name__ == "__main__":
    app = VivosunThermoApp()
    asyncio.run(app.run(sys.argv))
