from collections import namedtuple
from time import sleep
from enum import Enum

from serial import Serial, SerialException
from serial.tools.list_ports import comports


class BattLabOne:
    class CurrentRange(Enum):
        HIGH = 1
        LOW = 2

    @staticmethod
    def find_ports():
        names = []
        for port in list(comports()):
            if port.vid == 0x0403 and port.pid == 0x6001:
                if port.serial_number[:2] == 'BB':
                    names.append(port.device)

        return names if len(names) else None

    def __init__(self, port):
        self.serial = Serial(port, 115200, timeout=0.5)
        self._sense = self.CurrentRange.HIGH
        self._voltage = 0.0
        self.version = self._run_cmd("p", 1)[0]
        if self.version < 1003:
            raise ValueError("firmware version too old")

        self.reset()
        self._calib_vals()

    def _run_cmd(self, cmd, num_results=0):
        results = []
        try:
            # terminate any remaining output from firmware
            self.serial.write("y".encode())

            self.serial.write(cmd.encode())
            for _ in range(num_results):
                data = self.serial.read(2)
                results.append((data[0] << 8) | data[1])

            self.serial.write("y".encode())
        except SerialException as e:
            print("serial error: ", e)
            results = None

        return results

    def _calib_vals(self):
        VSettings = namedtuple("VSettings", "cal, offset, cmd")
        results = self._run_cmd("j", 17)

        # bug in firmware sends offet for 3.2 but not for cal
        # 3.2 cal value is same as 3.0 (as of firmware v1.03)
        results.insert(4, results[3])

        ADJ = [0.0, 0.0006, 0.001, 0.0, 0.0, 0.0073, 0.001, 0.0016, 0.002]
        CMD = ["a", "b", "c", "d", "o", "n", "e", "f", "g"]

        self.cal_offset = {}
        i = 0
        for v in [1.2, 1.5, 2.4, 3.0, 3.2, 3.6, 3.7, 4.2, 4.5]:
            self.cal_offset[v] = VSettings(cal=results[i] / 1000.0,
                                           offset=(results[i + 9] / 100000.0) + ADJ[i],
                                           cmd=CMD[i])
            i = i + 1

    def collect(self, dur):
        # 115200 bps is about 1152 Bps or 576 samples/sec
        results = self._run_cmd("z", int(dur * 576))
        scaled = []
        if self._sense == self.CurrentRange.HIGH:
            sense_scale = self.cal_offset[self._voltage].cal
            offset = 0
        else:
            sense_scale = 99
            offset = self.cal_offset[self._voltage].offset

        for raw in results:
            scaled.append((0.0025 * raw) / sense_scale - offset)

        return scaled

    def off(self):
        self._run_cmd("i")

    def reset(self):
        self._run_cmd("w")
        sleep(0.25)

    @property
    def current_range(self):
        return self._sense

    @current_range.setter
    def current_range(self, val):
        if val == self.CurrentRange.HIGH:
            self._run_cmd("l")
        elif val == self.CurrentRange.LOW:
            self._run_cmd("k")
        else:
            raise ValueError("invalid sense resistor specified")

        self._sense = val
        sleep(0.1)

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, val):
        if val == 0:
            self._run_cmd("i")
        else:
            self._run_cmd(self.cal_offset[val].cmd, 0)
            self._run_cmd("h")

        self._voltage = val
        sleep(0.1)

    @property
    def voltages(self):
        return list(self.cal_offset.keys())


def main():
    import sys

    ports = BattLabOne.find_ports()
    if not ports:
        sys.stderr.write("no BattLab-One units detected\n")
        sys.exit(1)

    bl1 = BattLabOne(ports[0])

    print("fw version: {}".format(bl1.version))
    print(bl1.voltages)

    bl1.current_range = BattLabOne.CurrentRange.HIGH

    bl1.voltage = 3.0

    data = bl1.collect(1.5)

    bl1.off()

    print(max(data), min(data), sum(data) / len(data))


if __name__ == "__main__":
    main()
