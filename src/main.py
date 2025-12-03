import logging
import json
from sdk.commands.move_coordinates_command import MoveCoordinatesParamsPosition
from sdk.manipulators.medu import MEdu


logger = logging.getLogger(__name__)


def run_test(host: str, client_id: str, login: str, password: str):
    """
    Run the test trajectory with background speed limiting

    Args:
        host: IP address of the manipulator
        client_id: Client ID for connection
        login: Login for manipulator authentication
        password: Password for manipulator authentication
    """

    # Connect to manipulator
    logger.info("Task 1 Test: Running test trajectory with speed limiting")
    logger.info(f"Connecting to {host} as {login}...")
    manipulator = MEdu(host, client_id, login, password)

    try:
        manipulator.connect()
        manipulator.get_control()

        logger.info("Connected successfully!")

        logger.info("TEST COMPLETED SUCCESSFULLY")

        manipulator.mgbot_conveyer.set_speed_motors(10)
        manipulator.mgbot_conveyer.set_led_color(255, 0, 0)
        dist = float("inf")
        sensor_data = json.loads(manipulator.mgbot_conveyer.get_sensors_data(True))
        while dist > 150:
            sensor_data = json.loads(manipulator.mgbot_conveyer.get_sensors_data(True))
            dist = sensor_data["DistanceSensor"]
            logger.info(f"Distance: {dist}")
        manipulator.mgbot_conveyer.set_speed_motors(0)
        manipulator.mgbot_conveyer.set_led_color(0, 255, 0)

    except Exception as e:
        logger.exception(f"Error during test: {e}", exc_info=True)
    finally:
        # Cleanup
        try:
            manipulator.stop_movement()
            manipulator.disconnect()
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
        default="//",
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

    run_test(args.host, args.client_id, args.login, args.password)


if __name__ == "__main__":
    main()
