import sys
import socket

import json

import os

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
        network_list = config.get("networks")
        for nw in network_list:
            wlan.wifi_connect(nw["ssid"], nw["password"])
            if wlan.wifi.isconnected():
                print("connected")
                return


    try_connect()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 34197))
    s.listen(5)

    conn = None
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
            if conn is None:
                print("waiting to connection")
                conn, addr = s.accept()
                print(f"Got a connection from {str(addr)}")
            data = conn.recv(1024)
            print(f"Content = {str(data)}")

            json_data = json.loads(data)
            try:
                request = json_data["header"]
            except KeyError:
                print("unknown data")
                continue

            if request == "getInfo":
                print("request for info")
                info = os.uname()
                networks = []
                for n in wlan.available_networks():
                    if n[0]:
                        networks.append(n[0].decode("utf-8"))
                networks_string = ",".join(networks)

                response = {"deviceId": config.get("deviceId"),
                            "deviceName": config.get("deviceName"),
                            "networks": networks_string,
                            "sysName": info[0],
                            "nodeName": info[1],
                            "release": info[2],
                            "version": info[3],
                            "machine": info[4]
                            }

                conn.send(json.dumps(response))
                print(response)
                continue
            if request == "setDataAndConnect":
                print("set data and connect")
                print(json_data)
                config.set("deviceId", json_data["deviceId"])
                config.set("deviceName", json_data["deviceName"])
                ssid = json_data["wifiSsid"]
                password = json_data["wifiPassword"]

                network_list = config.get("networks")
                for index, n in enumerate(network_list):
                    if n["ssid"] == ssid:
                        n["password"] = password
                        break
                    if index == len(network_list) - 1:
                        network_list.append({"ssid": ssid, "password": password})
                        break

                config.set("networks", network_list)
                wlan.access_point_down()
                wlan.wifi_connect(ssid, password)
                conn = None
                if wlan.wifi.isconnected():
                    print(f"connected to {ssid}")
                    continue





            # conn.send(b"Hello from ESP")
        sleep(0.1)
