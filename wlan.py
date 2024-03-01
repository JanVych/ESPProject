import time

import network
import json


class Wlan:
    def __init__(self):
        self.wifi = network.WLAN(network.STA_IF)
        self.access_point = network.WLAN(network.AP_IF)

        self.wifi_ssid = ""
        self.wifi_password = ""
        self.wifi_connection_timeout = 10

        self.access_point_ssid = "esp32-module"
        self.access_point_password = None
        self.access_point_security = 2

    def wifi_connect(self, ssid: str = None, password: str = None) -> None:
        if self.wifi.isconnected() and (not ssid or ssid == self.wifi_ssid):
            return
        self.wifi_ssid = ssid if ssid is not None else self.wifi_ssid
        self.wifi_password = password if password is not None else self.wifi_password

        self.wifi.active(True)
        self.wifi.config(reconnects=0)
        self.wifi.connect(self.wifi_ssid, self.wifi_password)
        timer = time.time() + self.wifi_connection_timeout

        print(f"connecting to: {self.wifi_ssid}")
        while not self.wifi.isconnected():
            if time.time() > timer:
                print(f"connection failed, code: {self.wifi.status()}")
                return
        print(f"connected to {self.wifi_ssid}")
        print(f"network config: {self.wifi.ifconfig()}")

    def wifi_disconnect(self) -> None:
        if self.wifi.active():
            self.wifi.active(False)
            print("disconnected from wifi")

    def available_networks(self) -> list[tuple[str, bytes, int, int, int]]:
        if not self.wifi.active():
            self.wifi.active(True)
            networks = self.wifi.scan()
            self.wifi.active(False)
            return networks
        return self.wifi.scan()

    def access_point_up(self) -> None:
        self.access_point.active(True)
        self.access_point.config(ssid=self.access_point_ssid,
                                 password=self.access_point_password,
                                 security=self.access_point_security)

    def access_point_down(self) -> None:
        self.access_point.active(False)
