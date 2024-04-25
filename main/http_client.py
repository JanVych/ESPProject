from asyncio import open_connection, StreamReader, StreamWriter
from json import loads as json_loads
from json import dumps as json_dumps


# https://github.com/DrTom/py-u-async-http-client

def destructure_url(url: str):
    try:
        protocol, _, host, path = url.split("/", 3)
    except ValueError:
        protocol, _, host = url.split("/", 2)
        path = ""
    protocol = protocol.strip(':')
    if protocol == "https":
        port = 443
        ssl = True
    else:
        port = 80
        ssl = False
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)
    return {"protocol": protocol,
            "host": host,
            "port": port,
            "path": path,
            "ssl": ssl}


def build_head(url: str, method: str, body: str = None, data_format: str = None) -> bytes:
    url_params = destructure_url(url)

    head = [f"{method} /{url_params['path']} HTTP/1.0", f"Host: {url_params['host']}", f"Accept: */*"]
    if data_format == "json":
        head.append(f"Content-Type: application/json")
    if body:
        head.append(f"Content-Length: {len(body)}")
    head.append("\r\n")
    return "\r\n".join(head).encode()


async def __open_connection(url: str) -> tuple[StreamReader, StreamWriter]:
    url_params = destructure_url(url)
    return await open_connection(url_params['host'],
                                 url_params['port'],)


async def __close_connection(sw: StreamWriter):
    sw.close()
    await sw.wait_closed()


async def __get_status(sr: StreamReader):
    status_line = ""
    try:
        status = {}
        status_line = await sr.readline()
        status_v, status_code_s, *status_rest = status_line.split(None, 2)
        status["http_version"] = status_v.decode()
        status["code"] = int(status_code_s)
        if len(status_rest) > 2:
            status['reason_phrase'] = status_rest[2].rstrip()
        return status
    except Exception:
        raise ValueError(f"Failed to parse the HTTP status line: {status_line}")


async def __send_request(sw: StreamWriter, url: str, method: str,
                         body: bytes = None, data_format: str = None):
    head = build_head(url, method, body, data_format)
    sw.write(head)
    if body:
        sw.write(body)
    await sw.drain()


async def __get_response(sr: StreamReader, data_format: str = None):
    response = {"status": await __get_status(sr), "headers": {}, "body": None}
    while True:
        header_line = await sr.readline()
        if not header_line or header_line == b'\r\n':
            break
        key, value = header_line.decode().split(":", 1)
        response["headers"][key] = value.strip()
    body = await sr.read()
    if data_format == "json" and body:
        try:
            response["body"] = json_loads(body.decode())
        except Exception as exp:
            raise exp
    else:
        response["body"] = body
    return response


async def request(url: str, method: str,
                  body: bytes = None, data_format: str = None):
    try:
        sr, sw = await __open_connection(url)
        try:
            await __send_request(sw, url, method, body, data_format)
            resp = await __get_response(sr, data_format)
            return resp
        except Exception as exp:
            return {"status": {"code": 800}, "error": exp}
        finally:
            await __close_connection(sw)
    except Exception as exp:
        return {"status": {"code": 800}, "error": exp}


async def get(url: str, data_format: str = None):
    return await request(url, "GET", data_format=data_format)


async def post(url: str, data: str | dict):
    data_format = None
    if isinstance(data, dict):
        data_format = "json"
        data = json_dumps(data).encode()
    elif isinstance(data, str):
        data = data.encode()
    elif not isinstance(data, bytes):
        return {"status": {"code": 800}, "error": "wrong data type"}
    return await request(url, "POST", data, data_format=data_format)
