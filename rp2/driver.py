import machine
import time

from ulab import numpy as np

#     function generateGammaTable(gamma, steps, resolution) {
#       var arr = new Array(steps).fill(0)
#         .map((x, i) => Math.pow(i, gamma))
#       arr = arr.map(x => x / Math.max(...arr))
#         .map(x => Math.min(resolution, Math.round(x * resolution)));
#       return arr;
#     }
#
#
#     function generate() {
#
#       var gamma = parseFloat(document.querySelector('#gamma').value);
#       var steps = parseFloat(document.querySelector('#steps').value);
#       var maxValue = parseFloat(document.querySelector('#maxValue').value);
#
#       var lookupTable = generateGammaTable(gamma, steps, maxValue);
#
#       var varName = 'gamma_lut';
#       var varType = maxValue < 256 ? 'uint8_t' : maxValue < 65535 ? 'uint16_t' : 'uint32_t';
#
#       var snippet = (
#         `// Gamma brightness lookup table <https://victornpb.github.io/gamma-table-generator>
# // gamma = ${gamma.toFixed(2)} steps = ${steps} range = 0-${maxValue}
# const ${varType} ${varName}[${steps}] = {
#   ${lookupTable.map((x, i) => String(x).padStart(4, ' ') + ((i + 1) % 16 === 0 ? ',\n  ' : ',')).join('')}};`);
#
#       output.innerText = snippet;
#       //copy(output);
#
#       plotChart(gamma, steps, maxValue, lookupTable);
#     }


class ProtocolDriver:
    def __init__(self, fixtures, channels, gamma=2.0):
        self.gamma_table = self.generate_gamma_table(gamma, 256, 255)
        self.fixtures = fixtures
        self.channels = channels
        self.output_buffer = bytearray(self.fixtures * self.channels)
        print(f'Buffer size: {len(self.output_buffer)} bytes, {self.fixtures} fixtures x {self.channels} channels')

    def write_f_array(self, data: np.ndarray):
        raise NotImplementedError

    def _apply_gamma(self, bit_array: np.ndarray) -> np.ndarray:
        corrected_array = np.array([int(self.gamma_table[int(x)]) for x in bit_array], dtype=np.uint8)
        return corrected_array

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
    def __init__(self, fixtures: int, channels: int):
        super().__init__(fixtures, channels)
        print(f'Initializing WS2812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (400, 850, 800, 450)

    def write_f_array(self, data):
        self.output_buffer[:] = np.ndarray(self._apply_gamma(self.to_8bit(data)), dtype=np.uint8).tobytes()
        machine.bitstream(self.pin, 0, self.timing, self.output_buffer)


class SK6812(ProtocolDriver):
    def __init__(self, fixtures: int, channels: int):
        super().__init__(fixtures, channels)
        print(f'Initializing SK6812 driver')
        self.pin = machine.Pin(15, machine.Pin.OUT)
        self.timing = (300, 900, 600, 600)  # Not confirmed

    def write_f_array(self, data):
        self.output_buffer[:] = data
        machine.bitstream(self.pin, 0, self.timing, self.output_buffer)


class DMX512(ProtocolDriver):
    def __init__(self, fixtures: int, channels: int):
        if fixtures * channels > 512:
            raise ValueError('DMX can support a max of 512 channels.')
        super().__init__(fixtures, channels)
        print(f'Initializing DMX512 driver')

    def write_f_array(self, data):

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