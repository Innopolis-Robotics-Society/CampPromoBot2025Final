import logging
import math
from time import sleep
from typing import Callable, Literal
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
    """
    Wrapper class for MEdu manipulator control.

    Provides simplified interface for manipulator control with additional
    utilities for coordinate-based movement, gripper control, audio playback,
    and conveyor integration.
    """

    logger = logging.getLogger("InnoMEdu")

    # Tool frame used for coordinate transformations
    coordinate_tool: str = "tool0"

    # Available audio files on the manipulator
    audio_files = {
        "alert.wav",
        "warning.wav",
        "sound.wav",
        "start.wav",
        "finish.wav",
        "wait.wav",
    }

    # Default GPIO interface names for MEdu
    DefaultGPIOInterfaces = Literal[
        "/dev/gpiochip4/e1_pin",
        "/dev/gpiochip4/e2_pin",
        "/dev/gpiochip4/nrst_pin",
        "/dev/gpiochip4/stop_key_pin",
        "/dev/gpiochip4/ext_rx_pin",
        "/dev/gpiochip4/ext_tx_pin",
    ]

    # Current state variables
    pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Joint angles of the manipulator: (base, shoulder, elbow) in radians"""

    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Cartesian position of end-effector: (x, y, z) in meters"""

    gpio_states: dict[str, float] = {}
    """Current states of GPIO pins"""

    # Private constants
    _USELESS_ROTATE = MoveCoordinatesParamsOrientation(0.0, 0.0, 0.0, 1.0)
    """Quaternion orientation (required by API but not used in our simplified interface)"""

    _EPS = 0.01
    """Accuracy threshold for position matching in meters"""

    _AUDIO_REMOTE_PATH = "/opt/promobot/share/pm_behavior_tree/resources/audio"
    """Remote path where audio files are stored on the manipulator"""

    def __init__(self, host: str, client_id: str, login: str, password: str):
        """
        Initialize the manipulator controller.

        Args:
            host: IP address of the manipulator
            client_id: Client identifier for connection
            login: Authentication login
            password: Authentication password
        """
        self.host = host
        self.login = login
        self.password = password
        self.medu = MEdu(host, client_id, login, password)
        self.conveyor = InnoConveyor(self.medu.mgbot_conveyer)

    def connect(self):
        """
        Establish connection to the manipulator and set up state handlers.

        This method:
        - Connects to the manipulator
        - Takes control of the device
        - Registers callbacks for GPIO, position, and joint state updates
        """
        self.medu.connect()
        self.medu.get_control()
        self.medu.set_gpio_states_handler(self._gpio_cb)
        self.medu.set_coordinates_handler(self._position_cb)
        self.medu.set_joint_states_handler(self._pose_cb)

    def choose_tool(self, tool: str):
        """
        Select coordinate frame for position calculations.

        Args:
            tool: Tool frame name (typically 'tool0' or 'tool1')
        """
        self.coordinate_tool = tool

    def _position_cb(self, new_position):
        """
        Internal callback to update current end-effector position.

        Args:
            new_position: Position data from the manipulator
        """
        xyz = new_position[self.coordinate_tool]["position"]
        self.position = (xyz["x"], xyz["y"], xyz["z"])

    def _pose_cb(self, new_pose):
        """
        Internal callback to update current joint angles.

        Args:
            new_pose: Joint state data from the manipulator
        """
        joint_positions = new_pose["position"]
        # Extract first three joint positions (base, shoulder, elbow)
        self.pose = tuple([joint_positions[i] for i in range(3)])

    def _gpio_cb(self, gpio):
        """
        Internal callback to update GPIO states.

        Args:
            gpio: GPIO state data from the manipulator
        """
        for i in range(len(gpio["interface_names"])):
            self.gpio_states[gpio["interface_names"][i]] = gpio["values"][i]

    def get_gpio(self, name: DefaultGPIOInterfaces) -> float | None:
        """
        Get current value of a GPIO pin.

        Args:
            name: GPIO interface name

        Returns:
            GPIO value if available, None otherwise
        """
        return self.gpio_states.get(name)

    def gripper_on(self):
        """Enable power to the gripper/nozzle."""
        self.medu.nozzle_power(True)
        self.logger.info("Gripper power enabled")

    def set_gripper(self, rotation: int | None = None, gripper: int | None = None):
        """
        Control gripper position.

        Args:
            rotation: Gripper rotation angle in degrees (-88 to 90)
            gripper: Gripper opening in degrees (-90 open to 90 closed)
        """
        self.gripper_on()
        self.medu.manage_gripper(rotation=rotation, gripper=gripper)

    def to_coordinates(
        self,
        x: float,
        y: float,
        z: float,
        velocity: float = 0.5,
        acceleration: float = 0.5,
    ):
        """
        Move end-effector to target Cartesian coordinates (blocking).

        Args:
            x: Target x coordinate in meters
            y: Target y coordinate in meters
            z: Target z coordinate in meters
            velocity: Velocity scaling factor (0.0 to 1.0)
            acceleration: Acceleration scaling factor (0.0 to 1.0)
        """
        target_position = MoveCoordinatesParamsPosition(x, y, z)
        self.medu.move_to_coordinates(
            target_position,
            self._USELESS_ROTATE,
            velocity_scaling_factor=velocity,
            acceleration_scaling_factor=acceleration,
        )
        self.logger.info(f"Moved to {self.position}; joint angles: {self.pose}")

    def to_coordinates_task(
        self,
        x: float,
        y: float,
        z: float,
        task: Callable[[], None],
        task_frequency: int = 1,
    ):
        """
        Move to coordinates while executing a periodic task.

        Streams position commands to the manipulator while repeatedly calling
        the provided task function during movement.

        Args:
            x: Target x coordinate in meters
            y: Target y coordinate in meters
            z: Target z coordinate in meters
            task: Function to execute periodically during movement
            task_frequency: Execute task every N iterations (1 = every iteration)
        """
        self.medu.set_servo_control_type(ServoControlType.POSE)
        iteration_count = 0

        # Continue until position is reached within epsilon tolerance
        while (
            abs(self.position[0] - x) > self._EPS
            or abs(self.position[1] - y) > self._EPS
            or abs(self.position[2] - z) > self._EPS
        ):
            self.medu.stream_coordinates(
                MoveCoordinatesParamsPosition(x, y, z), self._USELESS_ROTATE
            )

            # Execute task at specified frequency
            iteration_count = (iteration_count + 1) % task_frequency
            if iteration_count == 0:
                task()

            sleep(0.025)  # 40 Hz update rate

        self.logger.info(f"Moved to {self.position}; joint angles: {self.pose}")

    def to_coordinates_gripper(
        self,
        x: float,
        y: float,
        z: float,
        gripper_angle: int,
        update_frequency: int = 1,
    ):
        """
        Move to coordinates while maintaining absolute gripper orientation.

        WARNING: The target gripper angle may be unreachable at certain points
        along the path due to mechanical constraints.

        Args:
            x: Target x coordinate in meters
            y: Target y coordinate in meters
            z: Target z coordinate in meters
            gripper_angle: Desired absolute gripper angle in degrees
            update_frequency: Update gripper every N iterations
        """

        def update_gripper_angle():
            # Calculate gripper angle compensating for base rotation
            compensated_angle = int(
                min(
                    90.0,
                    max(
                        -45.0,
                        gripper_angle + self.pose[0],  # Add base joint angle
                    ),
                )
            )
            self.medu.manage_gripper(rotation=compensated_angle)

        self.to_coordinates_task(x, y, z, update_gripper_angle, freq=update_frequency)

    def play_audio(self, audio_filename: str):
        """
        Play an audio file on the manipulator.

        Args:
            audio_filename: Name of the audio file to play (must be loaded first)
        """
        if audio_filename not in self.audio_files:
            self.logger.error(f"Audio file not loaded: {audio_filename}")
            return

        try:
            self.medu.play_audio(audio_filename)
        except Exception as e:
            self.logger.error(f"Audio playback failed: {type(e).__name__}: {e}")

    def load_audio(self, source_path: str):
        """
        Upload an audio file to the manipulator.

        Args:
            source_path: Local path to the audio file
        """
        if not os.path.isfile(source_path):
            self.logger.error(f"File does not exist: {source_path}")
            return

        ssh_client = None
        try:
            # Establish SSH connection
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=self.host, username=self.login, password=self.password
            )

            # Upload file via SFTP
            with ssh_client.open_sftp() as sftp_client:
                remote_path = os.path.join(
                    self._AUDIO_REMOTE_PATH, os.path.basename(source_path)
                )
                sftp_client.put(source_path, remote_path)
                self.audio_files.add(os.path.basename(source_path))
                self.logger.info(f"Successfully uploaded audio: {source_path}")

        except Exception as e:
            self.logger.exception(f"Audio upload failed: {type(e).__name__}: {e}")
        finally:
            if ssh_client:
                ssh_client.close()
