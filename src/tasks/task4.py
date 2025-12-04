import json
import logging
import math
from time import sleep, time
from sdk.commands.move_coordinates_command import MoveCoordinatesParamsPosition
from sdk.utils.enums import ServoControlType
from utils.innomedu import InnoMEdu


logger = logging.getLogger(__name__)


def task4(manip: InnoMEdu):
    led_t = time()
    led_s = 0
    led_pin = "/dev/gpiochip4/e1_pin"
    button_pin = "/dev/gpiochip4/e2_pin"
    flfl = True
    length = 0.3
    height = 0.3
    manip.medu.set_servo_control_type(ServoControlType.POSE)
    while True:
        button_state = manip.get_gpio(button_pin)
        is_button = (button_state if button_state is not None else 1.0) == 0.0
        if is_button:
            if time() - led_t > 1.0 - manip._EPS:
                led_s = 1 - led_s
                manip.medu.write_gpio(led_pin, led_s)
                led_t = time()
                if led_s == 0:
                    manip.set_gripper(gripper=-90)
                else:
                    manip.set_gripper(gripper=90)
            if flfl:
                new_angle = (
                    math.atan2(manip.position[1], manip.position[0]) - math.pi / 6
                )
                manip.medu.stream_coordinates(
                    position=MoveCoordinatesParamsPosition(
                        x=length * math.cos(new_angle),
                        y=length * math.sin(new_angle),
                        z=height,
                    ),
                    orientation=manip._USELESS_ROTATE,
                )
            else:
                new_angle = (
                    math.atan2(manip.position[1], manip.position[0]) + math.pi / 6
                )
                manip.medu.stream_coordinates(
                    position=MoveCoordinatesParamsPosition(
                        x=length * math.cos(new_angle),
                        y=length * math.sin(new_angle),
                        z=height,
                    ),
                    orientation=manip._USELESS_ROTATE,
                )
            if manip.pose[0] >= 0.67:
                flfl = False
            elif manip.pose[0] <= -0.67:
                flfl = True
        else:
            manip.medu.write_gpio(led_pin, 0)
        logger.info(f"Button: {is_button}, all gpios: {manip.gpio_states}")
        sleep(0.1)
