import logging
import os
import sys
from time import time
from typing import Callable
import json
import tests
from utils.innomedu import InnoMEdu
from time import sleep, time
from sdk.commands.move_coordinates_command import MoveCoordinatesParamsPosition, MoveCoordinatesParamsOrientation


COLOR_POSE_CONV = 3
COLOR_PROX_TRIGGER = 30
PICK_POSE_CONV = 130
PICK_POSE = [[0.248, 0.17, 0.19], [0.248, 0.17, 0.27], 26]
PICK_TRASH_POSE = [[0.25, -0.10, 0.19], [0.25, -0.11, 0.27], -26]
THROW_POSE = [[0.252, -0.2, 0.19], [0.252, -0.2, 0.27], -35]
TRASH_POSE = [[0.33, 0.0, 0.19], [0.33, 0.0, 0.27], 0]
USLESS_SILLY_THING = MoveCoordinatesParamsOrientation(0, 0, 0, 1)


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

def get_color(manip: InnoMEdu):
    manip.medu.mgbot_conveyer.set_speed_motors(7)
    manip.conveyor.set_led(255, 0, 0)
    dist = float("inf")
    prox = 0
    sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
    while (dist > COLOR_POSE_CONV and prox < COLOR_PROX_TRIGGER):
        sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
        dist = sensor_data["DistanceSensor"]
        prox = sensor_data["ColorSensor"]["Prox"]
        logger.info(f"Distance: {dist}")
    manip.medu.mgbot_conveyer.set_speed_motors(0)
    manip.conveyor.set_led(0, 255, 0)
    sleep(1)
    color = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))["ColorSensor"]
    logger.info(f"Color: {color}")
    return color

def to_pick_place(manip: InnoMEdu):
    logger.info(f"Go to pick place")
    manip.medu.mgbot_conveyer.set_speed_motors(7)
    manip.conveyor.set_led(255, 0, 0)
    dist = float("inf")
    sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
    while (dist > PICK_POSE_CONV):
        sensor_data = json.loads(manip.medu.mgbot_conveyer.get_sensors_data(True))
        dist = sensor_data["DistanceSensor"]
        logger.info(f"Distance: {dist}")
    manip.medu.mgbot_conveyer.set_speed_motors(0)
    manip.conveyor.set_led(0, 255, 0)

def pick_and_place(manip: InnoMEdu, pick_point, place_point):
    logger.info(f"Pick & place scenario")
    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*pick_point[1]),
    USLESS_SILLY_THING, 0.2, 0.2)

    manip.set_gripper(pick_point[2], -88)

    sleep(1)

    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*pick_point[0]),
    USLESS_SILLY_THING, 0.2, 0.2)

    manip.set_gripper(pick_point[2], 10)

    sleep(1)

    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*pick_point[1]),
    USLESS_SILLY_THING, 0.2, 0.2)

    logger.info(f"Get object")

    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*place_point[1]),
    USLESS_SILLY_THING, 0.2, 0.2)

    manip.set_gripper(place_point[2], 10)

    sleep(1)

    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*place_point[0]),
    USLESS_SILLY_THING, 0.2, 0.2)

    manip.set_gripper(place_point[2], -88)

    sleep(1)

    manip.medu.move_to_coordinates(
    MoveCoordinatesParamsPosition(*place_point[1]),
    USLESS_SILLY_THING, 0.2, 0.2)


    logger.info(f"Throw object")

def task_common(manip: InnoMEdu):
    
    init_color = get_color(manip)

    filtered_color = {k: v for k, v in init_color.items() if k != 'Prox'}

    targer_color = max(filtered_color, key=filtered_color.get)
    
    logger.info(f"Target color: {targer_color}")
    
    to_pick_place(manip)
    pick_and_place(manip, PICK_POSE, THROW_POSE)

    while True:

        sleep(5)

        new_color = get_color(manip)

        new_filtered_color = {k: v for k, v in new_color.items() if k != 'Prox'}

        color = max(new_filtered_color, key=new_filtered_color.get)

        logger.info(f"Find color: {color}")

        if color == targer_color:
            to_pick_place(manip)
            pick_and_place(manip, PICK_POSE, THROW_POSE)
        else:
            pick_and_place(manip, PICK_TRASH_POSE, TRASH_POSE)

    #pick_and_place(manip, PICK_POSE, TRASH_POSE)

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

    run_test(args.host, args.client_id, args.login, args.password, task_common)


if __name__ == "__main__":
    main()
