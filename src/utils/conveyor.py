import json
from sdk.manipulators.extern_devices.mgbot.mgbot_conveyer import MGbotConveyer


class InnoConveyor:
    def __init__(self, mgbot_conveyer: MGbotConveyer):
        self.conveyor = mgbot_conveyer

    def get_color(self) -> dict[str, int]:
        """Dictionary keys: R, G, B, Prox"""
        data = json.loads(self.conveyor.get_sensors_data())
        return data["ColorSensor"]
