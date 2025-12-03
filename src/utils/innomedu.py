import math
from typing import Callable

from sdk.manipulators.medu import MEdu

from utils.conveyor import InnoConveyor


class InnoMEdu:
    coordinate_tool: str = "tool0"

    pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gpio_states: dict[str, float] = {}

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
