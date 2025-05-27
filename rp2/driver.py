import machine
import time

class ProtocolDriver:
    def __init__(self, fixtures, channels):
        self.fixtures = fixtures
        self.channels = channels
        self.output_buffer = bytearray(self.fixtures * self.channels)
        print(f'Buffer size: {len(self.output_buffer)} bytes, {self.fixtures} fixtures x {self.channels} channels')

    def write_bytes(self, data):
        raise NotImplementedError


class WS2812(ProtocolDriver):
    def __init__(self, fixtures: int, channels: int):
        super().__init__(fixtures, channels)
        print(f'Initializing WS2812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (400, 850, 800, 450)

    def write_bytes(self, data):
        self.output_buffer[:] = data
        machine.bitstream(self.pin, 0, self.timing, self.output_buffer)


class SK6812(ProtocolDriver):
    def __init__(self, fixtures: int, channels: int):
        super().__init__(fixtures, channels)
        print(f'Initializing SK6812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (300, 900, 600, 600)  # Not confirmed

    def write_bytes(self, data):
        self.output_buffer[:] = data
        machine.bitstream(self.pin, 0, self.timing, self.output_buffer)


class DMX512(ProtocolDriver):
    def __init__(self, fixtures: int, channels: int):
        if fixtures * channels > 512:
            raise ValueError('DMX can support a max of 512 channels.')
        super().__init__(fixtures, channels)
        print(f'Initializing DMX512 driver')

    def write_bytes(self, data):

        self.output_buffer[:] = data
        frame = bytearray([0x00]) + self.output_buffer
        debug = machine.Pin(1, machine.Pin.OUT)
        pin = machine.Pin(0, machine.Pin.OUT)
        pin.low()
        debug.high()
        time.sleep_us(55)   # measured as ~90ms
        pin.high()
        debug.low()

        pin = machine.UART(0)
        pin.init(250_000, bits=8, parity=None, stop=2)

        pin.write(frame)


DRIVERS = {'WS2812': WS2812, 'SK6812': SK6812, "DMX512": DMX512}