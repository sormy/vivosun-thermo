from typing import Literal


def format_temperature(value: float, unit: Literal["c", "f"] = "c"):
    suffix = "°C" if unit == "c" else "°F"
    return f"{round(value, 1):.1f}{suffix}"


def format_humidity(value: float):
    return f"{round(value, 0):.0f}%"


def format_vpd(value: float):
    return f"{round(value, 2):.2f} kPa"
