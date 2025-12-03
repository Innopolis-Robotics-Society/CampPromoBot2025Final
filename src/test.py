import json
import logging
import sys
from time import sleep

from sdk.manipulators.medu import MEdu

from utils.innomedu import InnoMEdu


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="====[%(asctime)s %(levelname)s] %(name)s: %(message)s",
)

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
        logger.info(manip.conveyor.get_color())
        sleep(1)
