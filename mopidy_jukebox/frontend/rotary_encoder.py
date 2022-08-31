import logging

import pykka
from RPi import GPIO
import pigpio
from mopidy import core

logger = logging.getLogger("mopidy_jukebox.rotary")
TRACE = 5


class RotaryEncoderFrontend(pykka.ThreadingActor, core.CoreListener):
    A_PIN = 5
    B_PIN = 6
    S_PIN = 16
    MAX_VOLUME = 100
    MAX_DC = 25

    LED_R = 12
    LED_G = 13

    def __init__(self, config, core):
        super(RotaryEncoderFrontend, self).__init__()
        self.core = core
        self._state = 0
        self._volume = 0
        self._mute = False
        self._p_r = False
        self._pi = None

    def on_start(self):
        self._pi = pigpio.pi()
        if not self._pi.connected:

            raise ConnectionError("Could not connect to pigpio deamon.")

        GPIO.setup(self.A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.S_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.setup(self.LED_R, GPIO.OUT)
        GPIO.setup(self.LED_G, GPIO.OUT)
        # self._p_r = GPIO.PWM(self.LED_R, 50)
        # self._p_g = GPIO.PWM(self.LED_G, 50)

        GPIO.add_event_detect(self.A_PIN, GPIO.BOTH, callback=self._on_rotation, bouncetime=10)
        # GPIO.add_event_detect(self.B_PIN, GPIO.BOTH, callback=self._on_rotation, bouncetime=10)
        GPIO.add_event_detect(self.S_PIN, GPIO.RISING, callback=self._on_button, bouncetime=10)

        self._state = GPIO.input(self.A_PIN) | GPIO.input(self.B_PIN) << 1

        assert self.core.mixer.set_volume(self.MAX_VOLUME // 2)
        self._volume = self.core.mixer.get_volume().get()

        self._mute = self.core.mixer.get_mute().get()

        if self._mute:
            # self._p_g.start(.0)
            self._pi.set_PWM_dutycycle(self.LED_G, 0)
            self._pi.set_PWM_dutycycle(self.LED_R, self.MAX_DC)
        else:
            # self._p_g.start(self._volume)
            # self._p_r.start(self._volume)
            dc = int(self._volume / self.MAX_VOLUME * self.MAX_DC)
            self._pi.set_PWM_dutycycle(self.LED_G, dc)
            self._pi.set_PWM_dutycycle(self.LED_R, 0)

        # GPIO.output(self.LED_G, True)

    def on_stop(self):
        # TODO: implement shutdown
        GPIO.cleanup()
        self._pi.stop()
        pass

    def on_failure(self, exception_type, exception_value, traceback):
        # TODO: implement failure
        GPIO.cleanup()
        self._pi.stop()
        pass

    def volume_changed(self, volume):
        logger.log(TRACE, f"volume changed: {volume}")
        self._volume = volume
        if not self._mute:
            # self._p_r.ChangeDutyCycle(volume)
            # self._p_g.ChangeDutyCycle(volume)

            dc = int(self._volume / self.MAX_VOLUME * self.MAX_DC)
            self._pi.set_PWM_dutycycle(self.LED_G, dc)
            # self._pi.set_PWM_dutycycle(self.LED_R, dc)

    def mute_changed(self, mute):
        logger.log(TRACE, f"mute changed: {mute}")
        self._mute = mute
        # GPIO.output(self.LED_G, not mute)
        if self._mute:
            self._pi.set_PWM_dutycycle(self.LED_G, 0)
            self._pi.set_PWM_dutycycle(self.LED_R, self.MAX_DC)
        else:
            # self._p_r.ChangeDutyCycle(self._volume)
            # self._p_g.ChangeDutyCycle(self._volume)
            dc = int(self._volume / self.MAX_VOLUME * self.MAX_DC)
            self._pi.set_PWM_dutycycle(self.LED_G, dc)
            self._pi.set_PWM_dutycycle(self.LED_R, 0)

    def _on_rotation(self, channel):
        self._state <<= 2
        self._state |= GPIO.input(self.A_PIN) | GPIO.input(self.B_PIN) << 1
        self._state &= 0x0F

        if self._state == 0x09 or self._state == 0x06:
            v = self._volume + 2
            v = min(max(v, 0), self.MAX_VOLUME)
            self.core.mixer.set_volume(v)
        elif self._state == 0x03 or self._state == 0x0C:
            v = self._volume - 2
            v = min(max(v, 0), self.MAX_VOLUME)
            self.core.mixer.set_volume(v)

    def _on_button(self, channel):
        # if GPIO.input(self.S_PIN):
            # logger.debug(f"button released {channel}")
        self.core.mixer.set_mute(not self._mute)
        # else:
        #     logger.debug(f"button pressed {channel}")
