from config import Config
from wlan import Wlan
import server

from asyncio import start_server, StreamReader, StreamWriter, sleep
from asyncio import run as asyncio_run, create_task
from json import loads as json_loads
from json import dumps as json_dumps

from machine import Pin
from os import uname
from gc import mem_free, mem_alloc, collect as gc_collect

server_mode = False


async def secondary_coroutine(wlan: Wlan, config: Config):
    address = "https://192.168.0.107:45455/api/modules"
    b_led = Pin(2, Pin.OUT)
    print("secondary enter")
    while True:
        print(f"free: {mem_free()} B")
        b_led.value(1)
        if wlan.wifi.isconnected():
            messages = {"deviceId": config.get("deviceId"),
                        "deviceName": config.get("deviceName"),
                        "freeMemory": mem_free(),
                        "allocatedMemory": mem_alloc()}
            response = await server.send_report(config.get("serverAddress"), messages)
            print(response)
        await sleep(2)
        b_led.value(0)
        await sleep(2)
        b_led.value(1)
        if wlan.wifi.isconnected():
            data = await server.get_data(address)
            print(data)
        await sleep(2)
        b_led.value(0)
        await sleep(2)
        gc_collect()


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

            response = {"header": "getInfo",
                        "deviceId": config.get("deviceId"),
                        "deviceName": config.get("deviceName"),
                        "availableNetworks": networks_string,
                        "sysName": info[0],
                        "microPythonVersion": info[3],
                        "machine": info[4]
                        }
            writer.write(json_dumps(response).encode())
            print(f"send: {response}")

    if header == "connect":
        print(f"data: {json_data}")
        config.set_and_save("deviceId", json_data["deviceId"])
        config.set_and_save("deviceName", json_data["deviceName"])
        ssid = json_data["wifiSsid"]
        password = json_data["wifiPassword"]
        network_list = config.get("networks")
        if network_list:
            for index, n in enumerate(network_list):
                if n["ssid"] == ssid:
                    n["password"] = password
                    break
                if index == len(network_list) - 1:
                    network_list.append({"ssid": ssid, "password": password})
                    break
        else:
            network_list = [{"ssid": ssid, "password": password}]
        config.set_and_save("networks", network_list)
        config.set_and_save("serverAddress", json_data["serverAddress"])
        wlan.wifi_connect(ssid, password)
        response = {"header": "setDataAndConnect",
                    "status": True,
                    "message": ""
                    }
        if wlan.wifi.isconnected():
            server_mode = False
        else:
            response["status"] = False
            response["message"] = "failed to connect to wifi"
        writer.write(json_dumps(response).encode())
        print(f"send: {response}")

    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    ssid = "TP-Link-29"
    password = "ac41.E9lz77"
    global server_mode
    wlan = Wlan()
    wlan.wifi_connect(ssid, password)
    config = Config("config.json")
    server = None

    task = create_task(secondary_coroutine(wlan, config))

    led = Pin(14, Pin.OUT)
    button = Pin(27, Pin.IN)

    #ecomax = Ecomax(16, 17)

    while True:
        await sleep(0)
        button_state = button.value()
        if button_state:
            print("button pressed")
            led.value(1)
            server_mode = True

            gc.collect()
            await sleep(1)
            led.value(0)

        if server_mode:
            if not server:
                wlan.wifi_disconnect()
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
