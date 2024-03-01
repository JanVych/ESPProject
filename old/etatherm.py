import time
import machine

# from constants import ETB, DLE, SOH

DLE = 0x10
SOH = 0x01
ETB = 0x17


class Etatherm:
    def __init__(self, rx, tx, baudrate=9600, bits=8, parity=None, stop=1):
        self.bus = machine.UART(1, baudrate, bits, parity, stop, timeout=1000, rx=machine.Pin(rx),
                                tx=machine.Pin(tx))
        self.bus.flush()
        self.station_address = 1
        self.frame_timeout = 6
        self.communication_attempts = 3

    def get_real_temperature(self, device_address: int) -> int:
        """
        get real temperature of device
        :param device_address: in range from 0 to 15
        """
        ram_address = 0x60 + device_address
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
        data = self.read_data(self.station_address, ram_address, 2)
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
        command = ((data_size - 1) << 4) & 0xFF | 0x0C
        for i in range(1, self.communication_attempts + 1):
            try:
                self.send_frame(station_address, ram_address, command, bytearray(2))
                response = self.read_frame(data_size)
                return response
            except (OSError, ValueError) as exp:
                if i == self.communication_attempts:
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
        for i in range(1, self.communication_attempts + 1):
            try:
                self.send_frame(station_address, ram_address, command, bytearray(2))
                response = self.read_frame(data_size)
                return
            except (OSError, ValueError) as exp:
                if i == self.communication_attempts:
                    raise exp

    def read_frame(self, data_size: int) -> bytes:
        """
        :param data_size:
        :return:
        """
        timeout = time.time() + self.frame_timeout
        buffer = bytearray(10 + data_size)
        while time.time() < timeout:
            if self.read(1) == 0xFF and self.read(1) == 0xFF and self.read(1) == DLE and self.read(1) == ETB:
                buffer[0] = 0xFF
                buffer[1] = 0xFF
                buffer[2] = DLE
                buffer[3] = ETB
                data = self.read(2 + data_size + 4)
                i = 4
                for d in data:
                    buffer[i] = d
                    i += i

                adds = 0x00
                xors = 0x00
                for b in buffer:
                    adds = (adds + b) & 0xFF
                    xors ^= b

                if adds == buffer[6 + data_size + 2] and xors == buffer[6 + data_size + 2]:
                    return buffer[4: 4 + data_size]
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

        print(data_size)
        print(len(buffer))
        buffer_index = 7
        for d in data:
            print(buffer_index)
            buffer[buffer_index] = d
            buffer_index += 1

        adds = 0x00
        xors = 0x00
        for i in range(data_size + 7):
            adds = (adds + buffer[i]) & 0xFF
            xors ^= buffer[i]

        buffer[data_size + 7] = adds
        buffer[data_size + 8] = xors
        buffer[data_size + 9] = 0xFF

        self.bus.write(buffer)

    def read(self, n) -> bytes:
        result = self.bus.read(n)
        if result is not None:
            return result
        raise OSError("Read timeout")

    def write(self, data) -> None:
        self.bus.write(data)
