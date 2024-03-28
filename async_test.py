import asyncio

code = """def test(x):
    for i in range(0, x):
        print(x ** i)
def run():
    test(10)"""

with open("code1.py", "w") as f:
    f.write(code)


async def secondary_coroutine():
    while True:
        print('secondary task running')
        await asyncio.sleep(1)
        try:
            import code1
            code1.run()
        finally:
            pass


async def main_coroutine():
    loop = asyncio.get_event_loop()
    task = loop.create_task(secondary_coroutine())
    i = 0
    while True:
        i += 1
        print(f'main task running: {i}')
        await asyncio.sleep(1)
        if i == 5:
            print("cancel task")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                if task.done():
                    print("task canceled")
        if i == 10:
            i = 0
            print("new task")
            task = loop.create_task(secondary_coroutine())


main_loop = asyncio.get_event_loop()

main_task = main_loop.create_task(main_coroutine())

main_loop.run_forever()
