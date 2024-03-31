from config import Config
from wlan import Wlan

from _thread import start_new_thread, exit
from asyncio import start_server, StreamReader, StreamWriter, sleep
from asyncio import run as asyncio_run
from json import loads as json_loads
from json import dumps as json_dumps

from machine import Pin
from os import uname
from gc import mem_free, mem_alloc, collect

from time import sleep as tsleep

thread_flag = False
server_mode = True


def thread_func():
    b_led = Pin(2, Pin.OUT)
    while thread_flag:
        print(f"allocated: {mem_alloc()} B")
        print(f"free: {mem_free()} B")
        b_led.value(1)
        tsleep(1)
        b_led.value(0)
        tsleep(1)
    exit()


async def handle_connection(reader: StreamReader, writer: StreamWriter,
                            wlan: Wlan, config: Config):
    print("handle connection")
    global server_mode
    data_bytes = await reader.read()
    data = data_bytes.decode()
    json_data = None
    header = None
    try:
        json_data = json_loads(data)
    except ValueError:
        print("cant convert to json")

    if json_data:
        try:
            header = json_data["header"]
            print(f"header: {header}")
        except KeyError:
            print("no data header")

        if header == "getInfo":
            info = uname()
            networks = []
            for n in wlan.available_networks():
                if n[0]:
                    networks.append(n[0].decode())
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
            writer.write(json_dumps(response).encode())
            print(f"send: {response}")

    if header == "setDataAndConnect":
        print(f"data: {json_data}")
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
        server_mode = False
        wlan.wifi_connect(ssid, password)

    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    wlan = Wlan()
    config = Config("config.json")
    server = None
    global server_mode
    global thread_flag
    pid = start_new_thread(thread_func, ())

    led = Pin(14, Pin.OUT)
    button = Pin(27, Pin.IN)

    while True:
        await sleep(0)
        button_state = button.value()
        if button_state:
            print("button pressed")
            led.value(1)
            server_mode = True
            #thread_flag = False
            wlan.wifi_disconnect()
            collect()
            await sleep(1)
            led.value(0)

        if server_mode:
            if not server:
                wlan.access_point_up()
                server = await start_server(lambda r, w: handle_connection(r, w, wlan, config),
                                            "", 34197)
                print("server listening")

        else:
            if server:
                wlan.access_point_down()
                server.close()
                await server.wait_closed()
                server = None
                print("server killed")


if __name__ == "__main__":
    asyncio_run(main())
