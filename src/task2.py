import logging
import os
import sys
from time import time, sleep
from typing import Callable

import tests
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
        manipulator.medu.connect()
        manipulator.medu.get_control()

        logger.info("Connected successfully!")

        x1, y1 = 0.13, 0.25
        x2, y2 = 0.23, -0.13

        h1 = 0.2
        h2 = 0.01
        vel = 0.5
        angle_to_close = 44
        angle_to_open = -88
        angle_to_up = 86
        angle_to_reverse = -88

        # Set up the gripper in proper orientation
        manipulator.set_gripper(angle_to_up, angle_to_open)
        sleep(1)

        # Move to position upper first clocks
        manipulator.to_coordinates(x1, y1, h1, velocity=vel)

        # Move manipulator lower and grab first clocks
        manipulator.to_coordinates(x1, y1, h2, velocity=vel)
        manipulator.set_gripper(angle_to_up, angle_to_close)
        sleep(1)

        # Move first clocks up and rotate it in 180 degrees
        manipulator.to_coordinates(x1, y1, h1, velocity=vel)
        manipulator.set_gripper(angle_to_reverse, angle_to_close)
        sleep(1)

        # Put first clocks on floor and open gripper
        manipulator.to_coordinates(x1, y1, h2, velocity=vel)
        manipulator.set_gripper(angle_to_reverse, angle_to_open)
        sleep(1)

        # Move manipulator upper again for safe trajectory navigation 
        manipulator.to_coordinates(x1, y1, h1, velocity=vel)

        # Move manipulator upper second clocks, open gripper, rotate in needed way, and wait left second to finish all movement correctly at 60 seconds
        manipulator.to_coordinates(x2, y2, h1, velocity=vel)
        sleep(40)
        manipulator.set_gripper(angle_to_up, angle_to_open)
        sleep(1)

        # Move manipulator lower to second clocks and grab them
        manipulator.to_coordinates(x2, y2, h2, velocity=vel)
        manipulator.set_gripper(angle_to_up, angle_to_close)
        sleep(1)

        # Move manipulator upper, and rotate it in 180 degrees
        manipulator.to_coordinates(x2, y2, h1, velocity=vel)
        manipulator.set_gripper(angle_to_reverse, angle_to_close)
        sleep(1)

        # Put second clocks on floor and open gripper
        manipulator.to_coordinates(x2, y2, h2, velocity=vel)
        manipulator.set_gripper(angle_to_reverse, angle_to_open)
        sleep(1)

        # Move manipulator upper and finish task
        manipulator.to_coordinates(x2, y2, h1, velocity=vel)

        logger.info("TASK 2 COMPLETED SUCCESSFULLY")

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

    run_test(
        args.host, args.client_id, args.login, args.password, tests.to_gripper_test
    )


if __name__ == "__main__":
    main()
