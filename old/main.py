import sys
import socket

from config import Config

from wlan import Wlan

wifi_ssid = "TP-Link-29"
wifi_password = "ac41.E9lz77"

access_point_password = "123456789"


def html_page(networks):
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Network Configuration</title>
    </head>
    <body>
        <h2>Network Configuration</h2>
        
        <h4>Network List</h4>

        <ul id="networkList"> """

    html_networks = ""
    for n in networks:
        if not n[0]:
            continue
        network_html = f"""
        <li>
            <strong>Network Name:</strong> {n[0].decode('utf-8')}<br>
            <strong>Signal Strength:</strong> {n[3]}<br>
            <strong>Security:</strong> {n[4]}<br>
            <strong>Hidden:</strong> {n[5]}
        </li>"""
        html_networks = "".join([html_networks, network_html])

    html_end = """
        </ul>
        <form action="#" method="post" id="networkForm">
            <label for="ssid">SSID:</label>
            <input type="text" id="ssid" name="ssid" required>
            <br>
    
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
            <br>
    
            <input type="submit" value="Connect">
        </form>
        </body>
        </html>"""
    return "".join([html_start, html_networks, html_end])


if __name__ == "__main__":
    print("\n{} initialized\n".format(sys.platform))
    wlan = Wlan()
    wlan.wifi_ssid = wifi_ssid
    wlan.wifi_password = wifi_password

    for nw in wlan.available_networks():
        print(nw)

    wlan.wifi_connect()

    config = Config("config.json")

    wlan.access_point_password = access_point_password
    wlan.access_point_up()
    print(wlan.access_point.ifconfig())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        print('Content = %s' % str(request))

        try:
            headers, body = request.split(b'\r\n\r\n', 1)

            params = body.split(b'&')
            ssid = params[0].split(b'=')[1].decode('utf-8')
            password = params[1].split(b'=')[1].decode('utf-8')

            print("SSID:", ssid)
            print("Password:", password)
            wlan.wifi.isconnected()
            wlan.wifi_connect(ssid=ssid, password=password)
            wlan.wifi.isconnected()
        except IndexError:
            pass

        response = html_page(wlan.available_networks())

        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
