from machine import UART, Pin
from time import ticks_ms, ticks_diff, ticks_add
from helpers import reduce
from struct import unpack
from asyncio import sleep, create_task, StreamReader

HEADER_START_DELIMITER = 0x68
FRAME_END_DELIMITER = 0x16

DATA_BROADCAST_FRAME_TYPE = 0x08


class Ecomax:
    def __init__(self, rx=21, tx=22, interval_sec=6):
        self.interval_sec = interval_sec
        self.rx = rx
        self.tx = tx

        self.__running_task = None
        self.__running = False
        self.float_positions = [[78, "mixer-temperature", None], [94, "flue-temperature", None],
                                [98, "tuv-temperature", None], [102, "boiler-temperature", None],
                                [110, "accu-upper-temperature", None], [114, "accu-lower-temperature", None],
                                [244, "lambda-state", None], [86, "outer-temperature", None],
                                [248, "oxygen", None]]

    def run(self):
        if not self.__running:
            self.__running = True
            self.__running_task = create_task(self.__run())

    async def stop(self):
        if self.__running:
            self.__running = False
            # self.__running_task.cancel()
            await self.__running_task

    def is_running(self):
        return self.__running

    async def __run(self):
        uart = None
        buffer = []
        buffer_size = 0
        frame_size = 0
        header = False
        while self.__running:
            if not uart:
                uart = StreamReader(UART(1, 115200, 8, None, 1, timeout=2000, rx=Pin(self.rx), tx=Pin(self.tx)))
            byte_read = await uart.read(1)
            if byte_read is None:
                print("read timeout")
                continue
            byte_read = ord(byte_read)
            buffer.append(byte_read)
            buffer_size = buffer_size + 1

            if byte_read == HEADER_START_DELIMITER and not header:
                len_low = await uart.read(1)
                len_high = await uart.read(1)
                buffer.append(ord(len_low))
                buffer.append(ord(len_high))
                frame_size = ord(len_low) + ord(len_high) * 256
                buffer_size = buffer_size + 2
                header = True
                continue
            if buffer_size == frame_size:
                crc = buffer[-2]
                calc_crc = reduce(lambda x, y: x ^ y, buffer[:-2])
                if byte_read == FRAME_END_DELIMITER and crc == calc_crc:
                    frame_type = buffer[7]
                    print(f"\nrecipient: {buffer[3]}, sender: {buffer[4]} frame type: {buffer[7]}")
                    if frame_type == DATA_BROADCAST_FRAME_TYPE:
                        self.decode_frame(buffer[8:-2])
                        uart.close()
                        uart = None
                        print("waiting for next interval")
                        await sleep(self.interval_sec)
                else:
                    print("frame fail")

                buffer = []
                buffer_size = 0
                frame_size = 0
                header = False

    def decode_frame(self, data):
        print("data:")
        for f in self.float_positions:
            start = f[0]
            byte_string = bytes(data[start:start + 4])
            if len(byte_string) < 4:
                break
            value = unpack("<f", byte_string)[0]
            f[2] = value
            print(f"{f[1]}: {value}")
