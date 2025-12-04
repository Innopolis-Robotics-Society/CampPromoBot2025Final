import json
import logging
import math
from time import sleep, time

from sdk.commands.move_coordinates_command import MoveCoordinatesParamsPosition
from sdk.utils.enums import ServoControlType
from utils.innomedu import InnoMEdu

logger = logging.getLogger(__name__)


def task4(manip: InnoMEdu):
    """
    Task 4:
    - Toggle LED every second while the button is held.
    - Move the toolhead in a circular oscillation around the vertical axis.
    - Motion direction flips when the x-coordinate passes thresholds.
    """

    # GPIO configuration
    led_last_toggle = time()
    led_value = 0
    led_pin = "/dev/gpiochip4/e1_pin"
    button_pin = "/dev/gpiochip4/e2_pin"

    # Motion parameters
    oscillation_direction_forward = True
    radius_xy = 0.3
    z_height = 0.3

    manip.medu.set_servo_control_type(ServoControlType.POSE)

    while True:
        # Read button state (the GPIO sometimes returns None)
        raw_button = manip.get_gpio(button_pin)
        button_pressed = (raw_button if raw_button is not None else 1.0) == 0.0

        if button_pressed:
            # LED toggle once per second
            if time() - led_last_toggle > 1.0 - manip._EPS:
                led_value = 1 - led_value
                manip.medu.write_gpio(led_pin, led_value)
                led_last_toggle = time()

            # Compute new angle around Z
            current_angle = math.atan2(manip.position[1], manip.position[0])

            # Adjust angle depending on oscillation direction
            if oscillation_direction_forward:
                target_angle = current_angle - math.pi / 6
            else:
                target_angle = current_angle + math.pi / 6

            # Send streaming pose
            manip.medu.stream_coordinates(
                position=MoveCoordinatesParamsPosition(
                    x=radius_xy * math.cos(target_angle),
                    y=radius_xy * math.sin(target_angle),
                    z=z_height,
                ),
                orientation=manip._USELESS_ROTATE,
            )

            # Flip oscillation direction based on pose limits
            if manip.pose[0] >= 0.67:
                oscillation_direction_forward = False
            elif manip.pose[0] <= -0.67:
                oscillation_direction_forward = True

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

    # Redirect normal stdout to a log file
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
