import logging
import os
import sys
from time import time
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

        # Dictionary from angles to positions
        positions = {
            0: (0.30, 0.0, 0.3),
            30: (0.26, -0.15, 0.3),
            60: (0.15, -0.26, 0.3),
            90: (0.00, -0.30, 0.3)
        }

        # Some variables for movement logic
        previous_angle = None
        previous_dist = 0
        angle = 0
        sound = 0

        # Main loop
        while True:
            # Get distance from distance sensor on conveyor
            dist = manipulator.conveyor.get_distance()
            logger.info(f"Distance: {dist}")

            # 4 Cases of distances and their respective angles and sound effects 
            if abs(dist - previous_dist) > 10:
                if 500 >= dist >= 400: # Case for distance in interval [400, 500]
                    if previous_angle != 0:
                        angle = 0
                        sound = 0
                elif 200 <= dist < 400: # Case for distance in interval [200, 400)
                    if previous_angle != 30:
                        angle = 30
                        sound = 1
                elif 100 <= dist < 200: # Case for distance in interval [100, 200)
                    if previous_angle != 60:
                        angle = 60
                        sound = 3
                elif dist < 100: # Case for distance in interval [0, 100)
                    if previous_angle != 90:
                        angle = 90
                        sound = 10000
                else: # Case when difference between two last distances is lower than 10 (we consider this change as non-effective)
                    angle = previous_angle
                    sound = 0
                previous_dist = dist
                
            # Check is previous assignment of angle was on equal angle value
            if previous_angle != angle:
                # Get coordinates of point for given angle of rotation by z (yaw) axis, and move manipulator in this point
                x, y, z = positions[angle]
                manipulator.to_coordinates(x, y, z, velocity=0.5, acceleration=0.5)
                logger.info(f"Moved to angle {angle}, Distance: {dist}")


            previous_angle = angle
            if sound != 0: # If there left number of sound warnings, do play sound
                manipulator.play_audio("warning.wav")
                sound -= 1

        logger.info("TASK 3 COMPLETED SUCCESSFULLY")

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
        default="10.87.14.122",
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
