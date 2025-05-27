import time
from machine import Pin
import neopixel

pin0 = Pin(0, Pin.OUT)
np = neopixel.NeoPixel(Pin(12), 3)
pin0.value(0)
np.fill((10, 0, 0))
np.write()
time.sleep(0.5)
pin0.value(1)
np.fill((0, 10, 0))
np.write()
