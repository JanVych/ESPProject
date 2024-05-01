from http_client import get


class Communicator:
    def __init__(self, address: str, device_id: str, device_name: str):
        self.address = address
        self.device_name = device_name
        self.device_id = device_id
        self.interval = 10
        self.orders = {}

        self.__create_message()

    def __create_message(self) -> None:
        self.message = {"deviceId": self.device_id, "deviceName": self.device_name}

    def register_callback(self, name: str, callback: callable) -> None:
        self.orders[name] = callback

    def add_message(self, name: str, value) -> None:
        self.message[name] = value
