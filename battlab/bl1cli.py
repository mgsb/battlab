"""Command-line utility for making measurement using BattLab-One"""

__copyright__ = "Copyright (c) 2021 Mark Grosen <mark@grosen.org>"
__license__ = "SPDX-License-Identifier: MIT"

import sys
import argparse
from time import sleep

from battlab import BattLabOne


def main():
    argp = argparse.ArgumentParser(description="Measure current with BattLab-One")
    argp.add_argument("-c", "--current-range", default="high",
                      choices=["high", "low"],
                      help="use high or low current range")
    argp.add_argument("-d", "--duration", default=1, type=int,
                      help="duration of measurement (seconds)")
    argp.add_argument("-g", "--graph", action="store_true",
                      help="graph (plot) the sample data")
    argp.add_argument("--no-reset", default=False, action="store_true",
                      help="do not reset device")
    argp.add_argument("-o", "--output", default=None,
                      help="output file to store sample data in")
    argp.add_argument("-p", "--port", default=None,
                      help="serial (com) port to use")
    argp.add_argument("-v", "--voltage", default=1.2,
                      type=float, help="voltage for testing")
    argp.add_argument("-w", "--wait", default=0, type=float,
                      help="wait seconds before sampling")

    args = argp.parse_args()

    ports = BattLabOne.find_ports()
    if not ports:
        sys.stderr.write("no BattLab-One units detected\n")
        sys.exit(1)

    if args.port and args.port not in ports:
        sys.stderr.write("requested port ({}) does not have BattLab-One "
                         "connected\n".format(args.port))
        sys.exit(2)

    bl1 = BattLabOne(ports[0])

    if args.voltage not in bl1.VOLTAGES:
        sys.stderr.write("requested voltage ({}) not "
                         "supported\n".format(args.voltage))
        sys.exit(3)

    if not args.no_reset:
        bl1.reset()

    bl1.current_range = bl1.CurrentRange[args.current_range.upper()]
    bl1.voltage = args.voltage

    sleep(args.wait)

    data = bl1.sample_block(args.duration)

    bl1.voltage = 0

    stats = "max: {:.2f}, min: {:.2f}, avg: {:.2f}".format(max(data), min(data),
                                                           sum(data) / len(data))

    if args.graph:
        import plotext as plt

        plt.plot(data)
        plt.plotsize(80, 50)
        plt.title(stats)
        plt.show()
    else:
        print(stats)

    if args.output:
        with open(args.output, "w") as out:
            for cur in data:
                out.write("{:.2f}\n".format(cur))


if __name__ == "__main__":
    main()
