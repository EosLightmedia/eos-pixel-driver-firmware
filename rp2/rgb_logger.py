from math import sin

import machine
import time

from neopixel import NeoPixel


class RGBLogger:
    def __init__(self):
        self.pixels = NeoPixel(machine.Pin(12), 3)
    
    @staticmethod
    def colorize_input(value: float):
        if value > 0.95:
            return 0, 20, 0

        blue = int(value * 10.) + 10
        green = int(value * 20.)
        return 0, green, blue

    @staticmethod
    def colorize_processor(value: float):
        red = int((min(max(1 - value, 0.), 1.) * 40))
        return red, 10, 0

    def set_in1(self, value: float):
        self.pixels[2] = self.colorize_input(value)
        self.pixels.write()
        
    def set_in2(self, value: float):
        self.pixels[1] = self.colorize_input(value)
        self.pixels.write()

    def processing_ratio(self, value: float):
        if value == 0.:
            self.pixels[0] = (10, 0, 0)
        else:
            self.pixels[0] = self.colorize_processor(value)
        self.pixels.write()
    
    def cndl_error(self):
        print('CNDL ERROR')
        self.pixels.fill((10, 10, 0))

    def cndl_missing(self):
        print('CNDL MISSING')
        self.pixels.fill((10, 10, 10))
        
    def system_error(self):
        while True:
            self.pixels.fill((10, 0, 0))
            self.pixels.write()
            time.sleep_ms(500)
            self.pixels.fill((0, 0, 0))
            self.pixels.write()
            time.sleep_ms(500)

    def boot_sequence(self):
        uv = [0., 0.33, 0.66]
        colors = [(1, 0, 1), (1, 1, 0), (0, 1, 1)]
        focal = -1
        for color in colors:
            while focal < .5:
                focal += 0.1
                for i, x in enumerate(uv):
                    x += focal
                    v = int(min(max((pow(x, 2) * -8) + 1, 0), 1) * 25)
                    self.pixels[i] = (v * color[0], v * color[1], v * color[2])
                self.pixels.write()
                time.sleep_ms(1000 // 60)
            focal = -1
