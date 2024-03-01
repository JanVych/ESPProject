import network
import time


class Application:
    def __init__(self):
        self.wifi_ssid = "TP-Link_6E6A"
        self.wifi_password = "48884006"
        #self.wifi_ssid = "ASUS"
        #self.wifi_password = "L4bc.K8zcm"
        #self.wifi_ssid = "Krepenec"
        #self.wifi_password = "y4HJkldvf5erkl"
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi_connection_timeout = 8

    def wifi_connect(self):
        if self.wifi.isconnected():
            return
        self.wifi.active(True)
        self.wifi.config(reconnects=0)
        self.wifi.connect(self.wifi_ssid, self.wifi_password)
        timer = time.time() + self.wifi_connection_timeout

        while not self.wifi.isconnected():
            if time.time() > timer:
                print(f"connection failed, code: {self.wifi.status()}")
                return
        print(f"connected to {self.wifi_ssid}")
        print(f"network config: {self.wifi.ifconfig()}")

    def wifi_disconnect(self):
        self.wifi.active(False)
        print("disconnected from wifi")

    def available_networks(self):
        self.wifi.active(True)
        networks = self.wifi.scan()
        for n in networks:
            print(n)
