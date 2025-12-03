import math
from time import sleep
from typing import Callable

from sdk.commands.move_coordinates_command import (
    MoveCoordinatesParamsOrientation,
    MoveCoordinatesParamsPosition,
)
from sdk.manipulators.medu import MEdu

from utils.conveyor import InnoConveyor


class InnoMEdu:
    coordinate_tool: str = "tool0"

    pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gpio_states: dict[str, float] = {}

    _USELESS_ROTATE = MoveCoordinatesParamsOrientation(0.0, 0.0, 0.0, 1.0)
    _EPS = 0.005

    def __init__(self, host: str, client_id: str, login: str, password: str):
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

    def to_coordinates_task(
        self, x: float, y: float, z: float, task: Callable[[], None]
    ):
        while (
            abs(self.position[0] - x) > self._EPS
            or abs(self.position[1] - y) > self._EPS
            or abs(self.position[2] - z) > self._EPS
        ):
            self.medu.stream_coordinates(
                MoveCoordinatesParamsPosition(x, y, z), self._USELESS_ROTATE
            )
            task()
            sleep(0.025)

    def to_coordinates_gripper(
        self, x: float, y: float, z: float, gripper_angle: int, freq: int = 1
    ):
        grip_i = 0

        def task():
            nonlocal grip_i
            grip_i = (grip_i + 1) % freq
            if grip_i == 0:
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

        self.to_coordinates_task(x, y, z, task)
