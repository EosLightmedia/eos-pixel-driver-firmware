import gc
import json
import time

import machine
from ulab import numpy as np

from cndl import CNDL
from rgb_logger import RGBLogger
import driver


class EPD:
    def __init__(self):
        print('Booting...')
        self.logger = RGBLogger()
        self.logger.boot_sequence()

        print('Loading settings...')
        self.settings = {}

        try:
            with open('settings.json') as settings_file:
                self.settings = json.load(settings_file)
                print(f'Settings loaded: {self.settings}')
        except FileNotFoundError:
            print('No settings file found, using defaults')

        print('Applying settings...')
        self.fade_frames = int(self.settings.get('fade', 120))
        self.brightness = self.settings.get('brightness', 1.0)
        driver_type: type[driver.ProtocolDriver] = driver.DRIVERS.get(self.settings.get('protocol', 'WS2812'))

        print('Loading scene...')
        try:
            with open('.cndl') as cndl_file:
                data = json.load(cndl_file)

            self.cndl = CNDL(data)

            self.driver = driver_type(len(data['map']), len(data['personality']))

        except Exception as e:
            print(f"Failed to load scene: {e}")
            raise e
            self.logger.cndl_error()

        self.adc0 = machine.ADC(0)
        self.adc1 = machine.ADC(1)
        self.adc2 = machine.ADC(2)

    def run_scene(self):
        print('Running scene...')

        frame_time = 15900  # 16ms - offset (calculated via oscilloscope)
        fade_frames = int(self.fade_frames)

        while True:
            t = time.ticks_us()
            fade_frames -= 1 if fade_frames > 0 else 0
            fade = (1. - (fade_frames / self.fade_frames))

            in1 = self.read_in1()
            in2 = self.read_in2()
            self.logger.set_in1(in1)
            self.logger.set_in2(in2)
            self.cndl.update({'IN1': in1, 'IN2': in2})
            _bytes = np.array(self.cndl.output * 255 * fade * self.brightness, dtype=np.uint8).tobytes()

            self.driver.write_bytes(_bytes)

            gc.collect()
            elapsed = time.ticks_diff(time.ticks_us(), t)
            ratio = 1. - min(max((elapsed - frame_time) / frame_time, 0), 1)

            self.logger.processing_ratio(ratio)

            if elapsed < frame_time:
                time.sleep_us(frame_time - elapsed)

    def read_in1(self):
        return min(max(float((self.adc0.read_u16() / (2**16 - 256))), 0.0), 1.0)

    def read_in2(self):
        return min(max(float((self.adc1.read_u16() / (2**16 - 256))), 0.0), 1.0)

    def read_in3(self):
        return min(max(float((self.adc2.read_u16() / (2**16 - 1))), 0.0), 1.0)
