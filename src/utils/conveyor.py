import json
from sdk.manipulators.extern_devices.mgbot.mgbot_conveyer import MGbotConveyer


class InnoConveyor:
    """
    Wrapper class for MGbot conveyor control.

    Provides simplified interface for controlling the conveyor belt system
    including motors, sensors, LED, servo, buzzer, and display.
    """

    def __init__(self, mgbot_conveyer: MGbotConveyer):
        """
        Initialize the conveyor controller.

        Args:
            mgbot_conveyer: MGbot conveyor instance from the SDK
        """
        self._conveyer = mgbot_conveyer

    def get_color(self) -> tuple[tuple[int, int, int], int]:
        """
        Read color sensor data.

        Returns:
            Tuple containing:
                - RGB values as tuple (R, G, B) where each value is 0-255
                - Proximity value indicating object presence (0-255, higher = closer)
        """
        sensor_data = json.loads(self._conveyer.get_sensors_data(True))["ColorSensor"]
        rgb_values = (sensor_data["R"], sensor_data["G"], sensor_data["B"])
        proximity = sensor_data["Prox"]
        return (rgb_values, proximity)

    def get_distance(self) -> int:
        """
        Read distance sensor data.

        Returns:
            Distance measurement in millimeters
        """
        sensor_data = json.loads(self._conveyer.get_sensors_data(True))
        return sensor_data["DistanceSensor"]

    def set_servo(self, angle: int):
        """
        Set servo motor angle.

        Args:
            angle: Target angle in degrees
        """
        self._conveyer.set_servo_angle(angle)

    def set_led(self, red: int, green: int, blue: int):
        """
        Set LED color.

        Args:
            red: Red channel intensity (0-255)
            green: Green channel intensity (0-255)
            blue: Blue channel intensity (0-255)
        """
        self._conveyer.set_led_color(red, green, blue)

    def set_speed(self, speed: int):
        """
        Set conveyor belt motor speed.

        Args:
            speed: Motor speed value (0-100)
        """
        self._conveyer.set_speed_motors(speed)

    def set_buzz(self, tone: int):
        """
        Play buzzer tone.

        Args:
            tone: Tone level (1-15)
        """
        self._conveyer.set_buzz_tone(tone)

    def display_text(self, text: str):
        """
        Display text on the conveyor's screen.

        Args:
            text: Text string to display
        """
        self._conveyer.display_text(text)
