import logging
from threading import Event

import pykka
from mopidy import core

import board
import RPi.GPIO as GPIO

# INTRRPT_GPIO = 36
INTRRPT_GPIO = 23

# import board
from adafruit_neokey.neokey1x4 import NeoKey1x4


logger = logging.getLogger("mopidy_jukebox.neokeys")

PREV = 0
STOP = 1
PLPA = 2
NEXT = 3


class NeoKeysFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core: core.Core):
        super(NeoKeysFrontend, self).__init__()
        self.core = core
        self.neokeys_listener = None

    def on_start(self):
        self.neokeys_listener = NeoKeysListener.start(self.actor_ref.proxy())

    def on_stop(self):
        self.neokeys_listener.stop()

    def on_button_pressed(self, b):
        state = self.core.playback.get_state().get()
        logger.debug(f"state is {state}")
        if b == PREV:
            # TODO implement seeking
            logger.debug("calling previous()")
            self.core.playback.previous()
        elif b == STOP:
            logger.debug("calling stop()")
            self.core.playback.stop()
        elif b == PLPA:
            if state in (core.PlaybackState.PAUSED, core.PlaybackState.STOPPED):
                logger.debug("calling resume()")
                # TODO: resume does not work for PlaybackState.STOPPED
                self.core.playback.resume()
            elif state == core.PlaybackState.PLAYING:
                logger.debug("calling pause()")
                self.core.playback.pause()
        elif b == NEXT:
            # TODO implement seeking
            logger.debug("calling next()")
            self.core.playback.next()


class NeoKeysListener(pykka.ThreadingActor):
    def __init__(self, frontend: NeoKeysFrontend):
        super(NeoKeysListener, self).__init__()
        self.neokeys = None
        self.frontend = frontend

        self.neokey_released = [Event(), Event(), Event(), Event()]

    def on_start(self):
        GPIO.setup(INTRRPT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(INTRRPT_GPIO, GPIO.FALLING, callback=self.on_neokey_interrupt, bouncetime=50)

        self.neokeys = NeoKey1x4(board.I2C())
        self.neokeys.set_GPIO_interrupts(0xf0, True)

    def on_neokey_interrupt(self, channel):
        if channel != INTRRPT_GPIO:
            return
        flag = self.neokeys.get_GPIO_interrupt_flag(delay=0.05)
        logger.debug(f"butten pressed: ch: {channel} flag: {flag}")
        for i in range(4):
            if flag & (1 << 4+i):
                if self.neokeys[i]:
                    logger.debug(f"button {i} pressed")
                    self.neokey_released[i].clear()
                    self.frontend.on_button_pressed(i)
                else:
                    logger.debug(f"button {i} released")
                    self.neokey_released[i].set()


class NeoKeysLEDActor(pykka.ThreadingActor):
    def __init__(self):
        super(NeoKeysLEDActor, self).__init__()
        self.neokeys = None

    def on_start(self):
        self.neokeys = NeoKey1x4(board.I2C())

    def set_colors(self, colors):
        pass

    def set_color(self, i, color):
        pass

    def start_animation(self, animation):
        pass
