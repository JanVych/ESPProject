import sys
import time
import json
import os
import urequests as requests

from config import Config

from wlan_module import WlanModule

if __name__ == "__main__":
    print("\n{} initialized\n".format(sys.platform))
    app = WlanModule()
    app.available_networks()
    app.wifi_connect()

    config = Config("config.json")
    config.set("test", 20)
    print("test:")
    print(config.get("test"))

    res = requests.get(url='http://www.baidu.com/')
    print(res.text)

