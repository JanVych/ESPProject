from http_client import post, get


async def send_report(address: str, messages: dict) -> None | dict:
    response = await post(address, messages)
    print(response)
    if "body" in response and response["body"] is not None:
        return response["body"]


async def get_data(address: str) -> None | dict:
    response = await get(address, data_format="json")
    print(response)
    if "body" in response:
        return response["body"]