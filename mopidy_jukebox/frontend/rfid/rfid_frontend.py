import logging
import struct
import threading
import time
from time import sleep

import pykka
from mopidy import core
import RPi.GPIO as GPIO

from RC522_Python import RFID

from .tag_registry import TagRegistry

logger = logging.getLogger("mopidy_jukebox.rfid")


class RFIDFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RFIDFrontend, self).__init__()
        self.core = core
        self.reader = None
        self.listener = None

    def on_start(self):
        self.listener = RFIDListener(self.actor_ref.proxy())
        self.listener.start()

    def on_stop(self):
        self.listener.stop()
        self.listener.join()

    def on_tag_connect(self, tag_uid):
        logger.info(f"tag connected: {tag_uid}")
        pass

    def on_tag_disconnect(self, tag_uid):
        logger.info(f"tag disconnected: {tag_uid}")
        pass


class RFIDListener(threading.Thread):
    def __init__(self, frontend_proxy):
        super(RFIDListener, self).__init__()
        self.frontend_proxy: RFIDFrontend = frontend_proxy
        self.reader = RFID()

        self._running = True
        self._connected = False
        self._error_counter = 0
        self._tag_uid = None

    def run(self) -> None:
        while self._running:
            (error, data) = self.reader.request()
            if not error:
                (error, uid) = self.reader.anticoll()
                if not error:
                    _uid = 0
                    for i in range(5):
                        _uid = (_uid << 8) | uid[i]
                    if not self._connected or self._uid != _uid:
                        self.frontend_proxy.on_tag_connect(_uid)
                        self._connected = True
                        self._uid = _uid
                    self._error_counter = 0
                elif self._connected:
                    self._error_counter += 1
            elif self._connected:
                self._error_counter += 1

            if self._error_counter == 2:
                self._error_counter = 0
                self._connected = False
                self.frontend_proxy.on_tag_disconnect(self._uid)

            self.reader.init()
            time.sleep(.2)

        GPIO.cleanup()

    def stop(self):
        if self._running:
            self._running = False

# class RFIDListener(threading.Thread):
#     def __init__(self, frontend_proxy):
#         super(RFIDListener, self).__init__()
#         self.frontend_proxy: RFIDFrontend = frontend_proxy
#         self.reader = RFID(pin_rst=25, pin_irq=24, pin_mode=GPIO.BCM)
#         self._running = True
#         self._connected = False
#         self._tag_uid = None
#
#     def _uid2str(self, uid):
#         return "-".join(map(str, uid))
#
#     def run(self):
#         while self._running:
#             if not self._connected:
#                 self.reader.irq.wait(.2)
#                 (error, tag_type) = self.reader.request()
#                 if not error:
#                     (error, uid) = self.reader.anticoll()
#                     if not error:
#                         self._connected = True
#                         self._tag_uid = self._uid2str(uid)
#                         # print("tag detected. UID: " + self._tag_uid)
#                         self.frontend_proxy.on_tag_connect(self._tag_uid)
#             else:
#                 sleep(.5)
#                 (error, tag_type) = self.reader.request()
#                 if not error:
#                     (error, uid) = self.reader.anticoll()
#                     if not error:
#                         uid_str = self._uid2str(uid)
#                         if uid_str == self._tag_uid:
#                             continue
#                         else:
#                             logger.info(f"new tag detected. UID: {uid_str}")
#                             self.frontend_proxy.on_tag_disconnect(self._tag_uid)
#                             self._tag_uid = uid_str
#                             self.frontend_proxy.on_tag_connect(self._tag_uid)
#                     # else:
#                     #     self._connected = False
#                     #     self.frontend_proxy.on_tag_disconnect(self._tag_uid)
#                 else:
#                     self._connected = False
#                     self.frontend_proxy.on_tag_disconnect(self._tag_uid)
#
#     def stop(self):
#         if self._running:
#             self._running = False