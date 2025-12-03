from sdk.manipulators.medu import MEdu

from utils.conveyor import InnoConveyor


class InnoMEdu(MEdu):
    def __init__(self, host: str, client_id: str, login: str, password: str):
        super().__init__(host, client_id, login, password)
        self.conveyer = InnoConveyor(self.mgbot_conveyer)
