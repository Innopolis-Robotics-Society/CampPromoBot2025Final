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
        sleep(0.1)


if __name__ == "__main__":
    import logging
    import os
    import sys
    from time import time
    from typing import Callable

    from utils.innomedu import InnoMEdu

    _stdout = sys.stdout
    # comment the line below to see all the output
    sys.stdout = open(f"logs/out_{int(time())}.log", "w")
    logging.basicConfig(
        level=logging.INFO,
        stream=_stdout,
        format="====[%(asctime)s %(levelname)s] %(name)s: %(message)s",
    )

    logger = logging.getLogger(__name__)

    def run_test(
        host: str,
        client_id: str,
        login: str,
        password: str,
        test: Callable[[InnoMEdu], None],
    ):
        """
        Run the test trajectory with background speed limiting

        Args:
            host: IP address of the manipulator
            client_id: Client ID for connection
            login: Login for manipulator authentication
            password: Password for manipulator authentication
        """

        # Connect to manipulator
        logger.info(f"Connecting to {host} as {login}...")
        manipulator = InnoMEdu(host, client_id, login, password)

        try:
            manipulator.connect()

            logger.info("Connected successfully!")

            test(manipulator)

            logger.info("TEST COMPLETED SUCCESSFULLY")

        except Exception as e:
            logger.exception(f"Error during test: {e}", exc_info=True)
        finally:
            # Cleanup
            try:
                manipulator.medu.stop_movement()
                manipulator.medu.disconnect()
                logger.info("Disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting manipulator: {e}")

    def main():
        """Main CLI entry point"""
        import argparse

        parser = argparse.ArgumentParser(
            description="Task 1 Test: Running test trajectory with speed limiting"
        )

        parser.add_argument(
            "--host",
            type=str,
            default="10.5.0.2",
            help="IP address of the manipulator",
        )
        parser.add_argument(
            "--client-id",
            type=str,
            default="main",
            help="Client ID for connection",
        )
        parser.add_argument(
            "--login",
            type=str,
            default="promobot",
            help="Login for manipulator authentication",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="1",
            help="Password for manipulator authentication",
        )

        args = parser.parse_args()

        run_test(args.host, args.client_id, args.login, args.password, task4)

    main()
