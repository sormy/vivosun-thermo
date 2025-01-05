import math


def calculate_vpd(temperature_c: float, humidity: float) -> float:
    e_s = 0.6108 * math.exp((17.27 * temperature_c) / (temperature_c + 237.3))
    e_a = e_s * (humidity / 100)
    return e_s - e_a


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32
