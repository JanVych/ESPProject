import sys
import socket
import etatherm

from machine import Pin
from time import sleep

from config import Config

from wlan import Wlan

wifi_ssid = "TP-Link-29"
wifi_password = "ac41.E9lz77"

access_point_password = "123456789"

if __name__ == "__main__":
    print("\n{} initialized\n".format(sys.platform))

    led = Pin(14, Pin.OUT)
    button = Pin(27, Pin.IN)

    etatherm = etatherm.Etatherm(16, 17)

    while True:
        button_state = button.value()
        led.value(button_state)
        #print(button_state)
        if button_state:
            print("try read")
            print(etatherm.get_real_temperature(1))
        sleep(0.1)
