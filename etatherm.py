import time
import machine
import gc

# from constants import ETB, DLE, SOH

DLE = 0x10
SOH = 0x01
ETB = 0x17


class Etatherm:
    def __init__(self, rx, tx, baudrate=9600, bits=8, parity=None, stop=1):
        self.bus = machine.UART(1, baudrate, bits, parity, stop, timeout=10000, rx=machine.Pin(rx),
                                tx=machine.Pin(tx))
        self.bus.flush()
        self.station_address = 1
        self.frame_timeout = 10

    def get_real_temperature(self, device_address: int) -> int:
        """
        get real temperature of device
        :param device_address: in range from 0 to 15
        """
        ram_address = 0x60 + device_address
        gc.collect()
        print(f"collected")
        print(gc.mem_alloc())
        return self.get_temperature(device_address, ram_address)

    def get_desired_temperature(self, device_address: int) -> int:
        """
        get desired temperature of device
        :param device_address: in range from 0 to 15
        """
        ram_address = 0x70 + device_address
        return self.get_temperature(device_address, ram_address)

    def get_oz_temperature(self, device_address: int) -> int:
        """
        get oz temperature of device
        :param device_address: in range from 0 to 15
        """
        ram_address = 0x1104 + (device_address << 4) & 0xFF
        return self.get_temperature(device_address, ram_address)

    def get_temperature(self, device_address: int, ram_address: int) -> int:
        """
        """
        if device_address not in range(0, 16):
            raise ValueError
        data = self.read_data(self.station_address, ram_address, 1)
        if device_address == 14:
            return 3 * (data[0] & 0xFF) + 5
        return (data[0] & 0xFF) + 5

    def read_data(self, station_address: int, ram_address: int, data_size: int) -> bytes:
        """
        read data from etatherm controller
        :param station_address: in range from 0 to 255
        :param ram_address: 0x60 - real temperature
        :param data_size:
        :return:
        """
        command = ((data_size - 1) << 4) & 0xFF | 0x08
        try:
            self.send_frame(station_address, ram_address, command, bytearray(1))
            response = self.read_frame(data_size)
            return response
        except (OSError, ValueError) as exp:
            raise exp

    def write_data(self, station_address, ram_address, data) -> None:
        """
        write data to etatherm controller
        :param station_address: in range from 0 to 255
        :param ram_address: 0x60 - real temperature
        :param data:
        :return:
        """
        data_size = len(data)
        command = ((data_size - 1) << 4) & 0xFF | 0x0C
        try:
            self.send_frame(station_address, ram_address, command, bytearray(2))
            response = self.read_frame(data_size)
            print(f"response data {response}")
            return
        except (OSError, ValueError) as exp:
            raise exp

    def read_frame(self, data_size: int) -> bytes:
        """
        :param data_size:
        :return:
        """
        data_size *= 2
        timeout = time.time() + self.frame_timeout
        # 0xFF 0xFF DLE ETB Adr.Bus D0 data S0 S1 ADDS XORS
        buffer = bytearray(6 + data_size + 4)

        header = [0, 0, 0, 0]
        while time.time() < timeout:
            header.insert(0, self.read(1))
            header.pop()
            print([hex(val) for val in header])
            print(gc.mem_alloc())
            if header[3] == 0xFF and header[2] == 0xFF and header[1] == DLE and header[0] == ETB:
                buffer[0] = header[3]
                buffer[1] = header[2]
                buffer[2] = header[1]
                buffer[3] = header[0]
                data = self.read(2 + data_size + 4)
                i = 4
                for d in data:
                    buffer[i] = d
                    i += 1

                print(f"frame received: {buffer}")
                adds = 0x00
                xors = 0x00
                for b in buffer[2:-4]:
                    adds = (adds + b) & 0xFF
                    xors ^= b
                if adds == buffer[6 + data_size + 2] and xors == buffer[6 + data_size + 3]:
                    data = bytearray(int(data_size / 2))
                    i = 0
                    for j in range(6, 6 + data_size, 2):
                        data[i] = buffer[j]
                        i += 1
                    return data
                raise ValueError("crc error")
        raise OSError("Frame read timeout")

    def send_frame(self, station_address: int, ram_address: int, command: int, data: bytes) -> None:
        """
        :param station_address: in range from 0 to 255
        :param ram_address:
        :param command:
        :param data:
        """
        data_size = len(data)
        buffer = bytearray(10 + data_size)
        buffer[0] = DLE
        buffer[1] = SOH
        buffer[2] = (station_address >> 8) & 0xFF
        buffer[3] = station_address & 0xFF
        buffer[4] = (ram_address >> 8) & 0xFF
        buffer[5] = ram_address & 0xFF
        buffer[6] = command

        buffer_index = 7
        for d in data:
            buffer[buffer_index] = d
            buffer_index += 1

        adds = 0x00
        xors = 0x00
        for b in buffer[:-3]:
            adds = (adds + b) & 0xFF
            xors ^= b

        buffer[data_size + 7] = adds
        buffer[data_size + 8] = xors
        buffer[data_size + 9] = 0xFF

        print(f"send frame: {buffer}")
        self.bus.write(buffer)

    def read(self, n) -> bytes | int:
        result = self.bus.read(n)
        if result is not None:
            if n == 1:
                print(hex(result[0]))
                return result[0]
            return result
        raise OSError("Read timeout")

    def write(self, data) -> None:
        self.bus.write(data)
