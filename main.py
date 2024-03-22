import sys
import socket
import etatherm

from machine import Pin
from time import sleep

from config import Config

from wlan import Wlan

# wifi_ssid = "TP-Link-29"
# wifi_password = "ac41.E9lz77"

# access_point_password = "123456789"

if __name__ == "__main__":

    led = Pin(14, Pin.OUT)
    button = Pin(27, Pin.IN)

    # etatherm = etatherm.Etatherm(16, 17)

    wlan = Wlan()
    config = Config("config.json")


    def try_connect():
        networks = config.get("networks")
        for n in networks:
            wlan.wifi_connect(n["ssid"], n["password"])
            if wlan.wifi.isconnected():
                print("connected")
                return


    try_connect()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 34197))
    s.listen(5)

    while True:
        button_state = button.value()
        # led.value(button_state)
        # if button_state:
        #     print("try read real temperature")
        #     print(etatherm.get_real_temperature(8))
        if button_state:
            wlan.wifi_disconnect()
            wlan.access_point_up()
        if wlan.access_point.active():
            conn, addr = s.accept()
            print(f"Got a connection from {str(addr)}")
            data = conn.recv(1024)
            print(f"Content = {str(data)}")

            conn.send(b"Hello from ESP")
        sleep(0.1)
