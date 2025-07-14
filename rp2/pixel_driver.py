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
                print('Applying settings...')
        except OSError:
            print('No settings file found, using defaults')

        self.fade_frames = int(self.settings.get('fade', 120))
        self.brightness = self.settings.get('brightness', 1.0)
        driver_type: type[driver.ProtocolDriver] = driver.DRIVERS.get(self.settings.get('protocol', 'WS2812'))

        print('Loading scene...')
        try:
            with open('.cndl') as cndl_file:
                data = json.load(cndl_file)

            self.cndl = CNDL(data)
            self.driver = driver_type()

        except Exception as e:
            print(f"Failed to load scene: {e}")
            self.logger.cndl_error()
            raise e

        self.adc0 = machine.ADC(0)
        self.adc1 = machine.ADC(1)
        self.adc2 = machine.ADC(2)

    def run_scene(self):
        print('Running scene...')

        frame_time = 15900  # 16ms - offset (calculated via oscilloscope)
        fade_frames = int(self.fade_frames)
        last_time = time.ticks_ms()
        inputs = {}
        inputs.update(self.settings)

        while True:
            t = time.ticks_us()
            current_time = time.ticks_ms()
            delta_time = time.ticks_diff(current_time, last_time) / 1000.0  # Convert to seconds
            last_time = current_time

            fade_frames -= 1 if fade_frames > 0 else 0
            fade = 1.0 if self.fade_frames <= 1 else (1. - (fade_frames / self.fade_frames))

            in1 = self.read_in1()
            in2 = self.read_in2()
            inputs["IN1"] = in1
            inputs["IN2"] = in2
            self.logger.set_in1(in1)
            self.logger.set_in2(in2)

            # 50%
            self.cndl.update(inputs, delta_time)

            _filtered = (self.cndl.output * fade * self.brightness).reshape(-1)
            # 15%
            self.driver.write_f_array(_filtered)

            # 30%
            gc.collect()

            elapsed = time.ticks_diff(time.ticks_us(), t)
            ratio = 1.0 - ((elapsed / frame_time) - 1.0)
            self.logger.processing_ratio(ratio)

            if elapsed < frame_time:
                time.sleep_us(frame_time - elapsed)

    def read_in1(self):
        return min(max(float((self.adc0.read_u16() / (2**16 - 256))), 0.0), 1.0)

    def read_in2(self):
        return min(max(float((self.adc1.read_u16() / (2**16 - 256))), 0.0), 1.0)

    def read_in3(self):
        return min(max(float((self.adc2.read_u16() / (2**16 - 1))), 0.0), 1.0)
