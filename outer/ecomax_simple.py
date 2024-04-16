from machine import UART, Pin
from time import ticks_ms, ticks_diff, ticks_add
from main.helpers import reduce
from struct import unpack

HEADER_START_DELIMITER = 0x68
FRAME_END_DELIMITER = 0x16

DATA_BROADCAST_FRAME_TYPE = 0x08


class Ecomax:
    def __init__(self, rx=16, tx=17, timeout_ms=20000):
        self.timeout_ms = timeout_ms
        # self.__running_task = None
        # self.__running = False
        self.float_positions = [[78, "mixer-temperature", None], [94, "flue-temperature", None],
                                [98, "tuv-temperature", None], [102, "boiler-temperature", None],
                                [110, "accu-upper-temperature", None], [114, "accu-lower-temperature", None],
                                [244, "lambda-state", None], [86, "outer-temperature", None],
                                [248, "oxygen", None]]

    def get_data(self):
        buffer = []
        buffer_size = 0
        frame_size = 0
        header = False
        uart = UART(1, 115200, 8, None, 1, timeout=2000, rx=Pin(16), tx=Pin(17))
        uart.flush()

        deadline = ticks_add(ticks_ms(), self.timeout_ms)
        print("get data loop")
        while ticks_diff(deadline, ticks_ms()) > 0:
            byte_read = uart.read(1)
            if byte_read is None:
                print("read timeout")
                continue
            byte_read = ord(byte_read)
            buffer.append(byte_read)
            buffer_size = buffer_size + 1

            if byte_read == HEADER_START_DELIMITER and not header:
                len_low = ord(uart.read(1))
                len_high = ord(uart.read(1))
                buffer.append(len_low)
                buffer.append(len_high)
                frame_size = len_low + len_high * 256
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
                        return
                else:
                    print(f"frame fail,  type: {buffer[7]}")

                buffer = []
                buffer_size = 0
                frame_size = 0
                header = False

        print("framer read timeout")

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
