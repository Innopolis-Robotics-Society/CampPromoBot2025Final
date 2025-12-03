import json
import logging

from sdk.manipulators.medu import MEdu


logger = logging.getLogger(__name__)


def empty_test(manip: MEdu):
    pass


def conveyor_test(manip: MEdu):
    manip.mgbot_conveyer.set_speed_motors(10)
    manip.mgbot_conveyer.set_led_color(255, 0, 0)
    dist = float("inf")
    sensor_data = json.loads(manip.mgbot_conveyer.get_sensors_data(True))
    while dist > 150:
        sensor_data = json.loads(manip.mgbot_conveyer.get_sensors_data(True))
        dist = sensor_data["DistanceSensor"]
        logger.info(f"Distance: {dist}")
    manip.mgbot_conveyer.set_speed_motors(0)
    manip.mgbot_conveyer.set_led_color(0, 255, 0)
