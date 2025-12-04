import json
import logging
from time import sleep

from utils.innomedu import InnoMEdu


logger = logging.getLogger(__name__)


def empty_test(manip: InnoMEdu):
    pass


def conveyor_test(manip: InnoMEdu):
    manip.medu.mgbot_conveyer.set_speed_motors(10)
    manip.medu.mgbot_conveyer.set_led_color(255, 0, 0)
    dist = float("inf")
    sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
    while dist > 150:
        sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
        dist = sensor_data["DistanceSensor"]
        logger.info(f"Distance: {dist}")
    manip.medu.mgbot_conveyer.set_speed_motors(0)
    manip.medu.mgbot_conveyer.set_led_color(0, 255, 0)


def color_test(manip: InnoMEdu):
    while True:
        color_res = manip.conveyor.get_color()
        manip.conveyor.set_led(*color_res[0])
        manip.conveyor.display_text(f"Proximity: {color_res[1]}")
        logger.info(f"{manip.medu.mgbot_conveyer.get_sensors_data()}")
        sleep(1)


def to_gripper_test(manip: InnoMEdu):
    manip.gripper_on()
    logger.info("Gripper on")
    manip.to_coordinates_gripper(0.2, 0.15, 0.2, 45)
    manip.to_coordinates_gripper(0.25, 0.0, 0.2, 45)
    manip.to_coordinates_gripper(0.2, -0.15, 0.2, 45)
