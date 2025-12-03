import json
from sdk.manipulators.extern_devices.mgbot.mgbot_conveyer import MGbotConveyer


class InnoConveyor:
    def __init__(self, mgbot_conveyer: MGbotConveyer):
        self._conveyer = mgbot_conveyer

    def get_color(self) -> tuple[tuple[int, int, int], int]:
        """
        returns: ((R, G, B), Proximity)
        Proximity shows presense of an object before the sensor.
        """
        data = json.loads(self._conveyer.get_sensors_data())["ColorSensor"]
        return ((data["R"], data["G"], data["B"]), data["Prox"])

    def get_distance(self) -> int:
        """
        returns: distance (probably in millimeters)
        """
        data = json.loads(self._conveyer.get_sensors_data())
        return data["DistanceSensor"]

    def set_servo(self, angle: int):
        self._conveyer.set_servo_angle(angle)

    def set_led(self, R: int, G: int, B: int):
        self._conveyer.set_led_color(R, G, B)

    def set_speed(self, speed: int):
        self._conveyer.set_speed_motors(speed)

    def set_buzz(self, tone: int):
        """
        tone: from 1 to 15
        """
        self._conveyer.set_buzz_tone(tone)

    def display_text(self, text: str):
        self._conveyer.display_text(text)
