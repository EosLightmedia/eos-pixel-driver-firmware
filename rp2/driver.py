import machine
import time

from ulab import numpy as np


class ProtocolDriver:
    def __init__(self, gamma=2.0):
        self.gamma_table = self.generate_gamma_table(gamma, 256, 255)

    def write_f_array(self, data: np.ndarray):
        raise NotImplementedError

    def _apply_gamma(self, bit_array: np.ndarray) -> np.ndarray:
        return np.array(np.take(self.gamma_table, bit_array), dtype=np.uint8)


    @staticmethod
    def generate_gamma_table(gamma, steps, resolution):
        arr = np.arange(steps) ** gamma
        arr /= max(arr)
        arr *= resolution
        return arr

    @staticmethod
    def to_8bit(float_array: np.ndarray) -> np.ndarray:
        return np.ndarray(float_array * 255, dtype=np.uint8)



class WS2812(ProtocolDriver):
    def __init__(self, gamma=2.0):
        super().__init__(gamma)
        print(f'Initializing WS2812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (400, 850, 800, 450)

    def write_f_array(self, data):
        machine.bitstream(self.pin, 0, self.timing, self._apply_gamma(self.to_8bit(data)).tobytes())


class SK6812(ProtocolDriver):
    def __init__(self, gamma=2.0):
        super().__init__(gamma)
        print(f'Initializing SK6812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (300, 900, 600, 600)  # Not confirmed

    def write_f_array(self, data):
        machine.bitstream(self.pin, 0, self.timing, self._apply_gamma(self.to_8bit(data)).tobytes())


class DMX512(ProtocolDriver):
    def __init__(self, gamma=2.0):
        super().__init__(gamma)
        print(f'Initializing DMX512 driver')

    def write_f_array(self, data):
        frame = bytearray([0x00]) + self.to_bytearray(data)
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