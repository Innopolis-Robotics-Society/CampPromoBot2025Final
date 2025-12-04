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

    run_test(args.host, args.client_id, args.login, args.password, tests.color_test)


if __name__ == "__main__":
    main()
