import logging
import math
from time import sleep
from typing import Callable
import os
import paramiko

from sdk.commands.move_coordinates_command import (
    MoveCoordinatesParamsOrientation,
    MoveCoordinatesParamsPosition,
)
from sdk.manipulators.medu import MEdu
from sdk.utils.enums import ServoControlType

from utils.conveyor import InnoConveyor


class InnoMEdu:
    logger = logging.getLogger("InnoMEdu")
    coordinate_tool: str = "tool0"
    audio_files = {
        "alert.wav",
        "warning.wav",
        "sound.wav",
        "start.wav",
        "finish.wav",
        "wait.wav",
    }
    DefaultGPIOInterfaces = [
        "/dev/gpiochip4/e1_pin",
        "/dev/gpiochip4/e2_pin",
        "/dev/gpiochip4/nrst_pin",
        "/dev/gpiochip4/stop_key_pin",
        "/dev/gpiochip4/ext_rx_pin",
        "/dev/gpiochip4/ext_tx_pin",
    ]

    """Joint states of the manipulator from base to end-effector."""
    pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Cartesian position of end-effector of the manipulator."""
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """States of GPIO pins by names."""
    gpio_states: dict[str, float] = {}

    # useless but required
    _USELESS_ROTATE = MoveCoordinatesParamsOrientation(0.0, 0.0, 0.0, 1.0)
    # accuracy of positioning
    _EPS = 0.01
    # path where audio files stored on manipulator
    _AUDIO_REMOTE_PATH = "/home/promobot"

    def __init__(self, host: str, client_id: str, login: str, password: str):
        self.host = host
        self.login = login
        self.password = password
        self.medu = MEdu(host, client_id, login, password)
        self.conveyor = InnoConveyor(self.medu.mgbot_conveyer)
        self.medu.set_coordinates_handler(self._position_cb)
        self.medu.set_joint_states_handler(self._pose_cb)
        self.medu.set_gpio_states_handler(self._gpio_cb)

    def choose_tool(self, tool: str):
        """
        Coordinates are parsed depending on some 'tool' whatever it means.
        Choose different (usually 'tool0' and 'tool1' are available) if you need.
        """
        self.coordinate_tool = tool

    def _position_cb(self, new_position):
        """The handler to parse a current pose of the end-effector and update it."""
        xyz = new_position[self.coordinate_tool]["position"]
        self.position = (xyz["x"], xyz["y"], xyz["z"])

    def _pose_cb(self, new_pose):
        """The handler to parse current rotations of the joints and update them."""
        j = new_pose["position"]
        self.pose = tuple([j / math.pi * 180 for j in (j[0], j[1], j[2])])

    def _gpio_cb(self, gpio):
        """The handler to parse current GPIO states and update them."""
        for i in range(len(gpio["interface_names"])):
            self.gpio_states[gpio["interface_names"][i]] = gpio["values"][i]

    def gripper_on(self):
        self.medu.nozzle_power(True)
        self.logger.info("Gripper on")

    def to_coordinates(
        self,
        x: float,
        y: float,
        z: float,
        velocity: float = 1.0,
        acceleration: float = 1.0,
    ):
        """More convenient method to move to coordinates."""
        target = MoveCoordinatesParamsPosition(x, y, z)
        self.medu.move_to_coordinates(
            target,
            self._USELESS_ROTATE,
            velocity_scaling_factor=velocity,
            acceleration_scaling_factor=acceleration,
        )
        self.logger.info(f"Moved to {self.position}; pose: {self.pose}")

    def to_coordinates_task(
        self, x: float, y: float, z: float, task: Callable[[], None], freq: int = 1
    ):
        """
        Stream coordinates to manipulator and simultaneously do something else.
        task: actions to do while moving to the point; shouldn't be anything heavy
        freq: how many steps to wait before repeating the action
        """
        self.medu.set_servo_control_type(ServoControlType.POSE)
        rep_i = 0
        while (
            abs(self.position[0] - x) > self._EPS
            or abs(self.position[1] - y) > self._EPS
            or abs(self.position[2] - z) > self._EPS
        ):
            self.medu.stream_coordinates(
                MoveCoordinatesParamsPosition(x, y, z), self._USELESS_ROTATE
            )
            rep_i = (rep_i + 1) % freq
            if rep_i == 0:
                task()
            sleep(0.025)
        self.logger.info(f"Moved to {self.position}; pose: {self.pose}")

    def to_coordinates_gripper(
        self, x: float, y: float, z: float, gripper_angle: int, freq: int = 1
    ):
        """
        Go to the point while preserving absolute gripper angle. Be careful,
        since the angle may be unreachable at some moment on the path.
        gripper_angle: angle to preserve
        freq: how frequently to ensure the gripper angle
        """

        def task():
            deg = int(
                min(
                    90.0,
                    max(
                        -45.0,
                        gripper_angle
                        # + math.atan2(self.position[1], self.position[0]) / math.pi * 180,
                        + self.pose[0],
                    ),
                )
            )
            self.medu.manage_gripper(rotation=deg)

        self.to_coordinates_task(x, y, z, task, freq=freq)

    def play_audio(self, audio: str):
        """
        Play some audio on the manipulator. Need to be loaded on the manipulator,
        which is checked in the `self.audio_files` list.
        """
        if audio not in self.audio_files:
            self.logger.error(f"No such audio file loaded: {audio}")
        try:
            self.medu.play_audio(audio)
        except Exception as e:
            self.logger.error(f"Playing audio failed with {type(e).__name__}: {e}")

    def load_audio(self, source: str):
        """
        Load an audio file on the manipulator and add it to the list.
        """
        if not os.path.isfile(source):
            self.logger.error(f"File {source} does not exist")
            return
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=self.host, username=self.login, password=self.password
            )
            with ssh_client.open_sftp() as sftp_client:
                sftp_client.put(
                    source,
                    os.path.join(self._AUDIO_REMOTE_PATH, os.path.basename(source)),
                )
                self.audio_files.add(os.path.basename(source))
                self.logger.info(f"Successfully loaded {source}")
        except Exception as e:
            self.logger.exception(f"{type(e).__name__}: {e}")
        finally:
            if "ssh_client" in locals() and ssh_client:
                ssh_client.close()
