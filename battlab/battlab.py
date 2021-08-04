"""
Support for interacting with a BattLab-One current measurement device.

:class BattLabOne:
"""

__copyright__ = "Copyright (c) 2021 Mark Grosen <mark@grosen.org>"
__license__ = "SPDX-License-Identifier: MIT"

from collections import namedtuple
from time import sleep
from enum import Enum
from itertools import islice as take_n
import sys

from serial import Serial, SerialException
from serial.tools.list_ports import comports


class BattLabOne:
    """Configure and interact with BattLab-One"""

    class CurrentRange(Enum):
        """Specify the sense(shunt) resistor for high and low current ranges"""
        HIGH = 1
        LOW = 2

    class FWCmd(Enum):
        """Commands to send to firmware for each method"""
        RESET = b'w'
        CALIB_VALS = b'j'
        SAMPLE = b'z'
        SAMPLE_TRIGGER = b'x'
        VERSION = b'p'

        CTRLC = b'y'

        RANGE_HIGH = b'l'
        RANGE_LOW = b'k'

        VOLT_OFF = b'i'
        VOLT_ON = b'h'

        VOLT_1_2 = b'a'
        VOLT_1_5 = b'b'
        VOLT_2_4 = b'c'
        VOLT_3_0 = b'd'
        VOLT_3_2 = b'o'
        VOLT_3_6 = b'n'
        VOLT_3_7 = b'e'
        VOLT_4_2 = b'f'
        VOLT_4_5 = b'g'

    VOLTAGES = [1.2, 1.5, 2.4, 3.0, 3.2, 3.6, 3.7, 4.2, 4.5]

    VSettings = namedtuple("VSettings", "cal, offset, cmd")

    def __init__(self, port=None, voltage=None, current_range=CurrentRange.HIGH,
                 reset=False):
        """
        Create a BattLabOne object to manage device using specified serial port

        :param port: name of serial (com) port
        """
        if not port:
            port = self.find_ports()[0]

        self.serial = Serial(port, 115200, timeout=0.5)

        self.version = self._run_cmd(self.FWCmd.VERSION, 1)[0]
        if self.version < 1003:
            raise ValueError("firmware version too old: {}".format(self.version))

        if reset:
            self.reset()

        self._calib_vals()

        self.current_range = current_range

        if voltage:
            self.voltage = voltage

    def _run_cmd(self, cmd, num_results=0):
        if cmd not in self.FWCmd:
            raise ValueError("invalid FW cmd")

        results = []
        try:
            # terminate any remaining output from firmware
            self.serial.write(self.FWCmd.CTRLC.value)
            self.serial.flushInput()

            self.serial.write(cmd.value)
            for _ in range(num_results):
                data = self.serial.read(2)
                results.append((data[0] << 8) | data[1])

            # self.serial.write(self.FWCmd.CTRLC.value)
        except SerialException as ser_exc:
            sys.stderr.write("serial error: {}\n".format(ser_exc))

        return results

    _ADJ = [0.0, 0.0006, 0.001, 0.0, 0.0, 0.0073, 0.001, 0.0016, 0.002]
    _CMD = [FWCmd.VOLT_1_2, FWCmd.VOLT_1_5, FWCmd.VOLT_2_4,
            FWCmd.VOLT_3_0, FWCmd.VOLT_3_2, FWCmd.VOLT_3_6,
            FWCmd.VOLT_3_7, FWCmd.VOLT_4_2, FWCmd.VOLT_4_5]

    def _calib_vals(self):
        results = self._run_cmd(self.FWCmd.CALIB_VALS, 17)

        # bug in firmware sends offet for 3.2 but not for cal
        # 3.2 cal value is same as 3.0 (as of firmware v1.03)
        results.insert(4, results[3])

        self.cal_offset = {}
        for i, v in enumerate(self.VOLTAGES):
            setting = self.VSettings(results[i] / 1000.0,
                                     (results[i + 9] / 100000.0) + self._ADJ[i],
                                     self._CMD[i])
            self.cal_offset[v] = setting

    def sample(self, trigger=False):
        """
        Sample current readings from device as a generator

        :param trigger: use triggered sampling method
        :yields: next current sample
        """
        if self._crange == self.CurrentRange.HIGH:
            sense_scale = self.cal_offset[self._voltage].cal
            offset = 0
        else:
            sense_scale = 99
            offset = self.cal_offset[self._voltage].offset

        self._run_cmd(self.FWCmd.SAMPLE_TRIGGER if trigger else self.FWCmd.SAMPLE, 0)
        ready = not trigger
        sleep(0.25)

        while True:
            if not ready:
                sleep(0.001)
                ready = self.serial.in_waiting
                yield 0.0
            else:
                data = self.serial.read(2)
                if not data or (data[0] == 0xff and data[1] == 0xff):
                    break
                raw = (data[0] << 8) | data[1]
                yield (0.0025 * raw) / sense_scale - offset

    def sample_block(self, dur, trigger=False):
        """
        Gather a block of sample current readings from device

        :param dur: duration (in seconds) of collection
        :returns: list of float sample values in mA
        """
        # measured ~ 1180 samples/sec from BL1
        return list(take_n(self.sample(trigger), int(dur * 1180)))

    def reset(self):
        """Reset the BattLab-One device"""
        self._run_cmd(self.FWCmd.RESET)
        sleep(0.25)

    @property
    def current_range(self):
        """Get or set the current range"""
        return self._crange

    @current_range.setter
    def current_range(self, crange):
        if crange == self.CurrentRange.HIGH:
            self._run_cmd(self.FWCmd.RANGE_HIGH)
        elif crange == self.CurrentRange.LOW:
            self._run_cmd(self.FWCmd.RANGE_LOW)
        else:
            raise ValueError("invalid current range specified")

        self._crange = crange
        sleep(0.1)

    @property
    def voltage(self):
        """Get or set the output (PSU) voltage"""
        return self._voltage

    @voltage.setter
    def voltage(self, v_val):
        if v_val == 0:
            self._run_cmd(self.FWCmd.VOLT_OFF)
        else:
            self._run_cmd(self.cal_offset[v_val].cmd, 0)
            self._run_cmd(self.FWCmd.VOLT_ON)

        self._voltage = v_val
        sleep(0.1)

    @staticmethod
    def find_ports():
        """
        Find serial (com) port(s) with BattLab-One attached

        :returns: list of serial (com) port names
        """
        names = []
        for port in list(comports()):
            if port.vid == 0x0403 and port.pid == 0x6001:
                if port.serial_number and port.serial_number[:2] == 'BB':
                    names.append(port.device)

        return names
