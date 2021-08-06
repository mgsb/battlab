import sys

from battlab import BattLabOne


def main():
    """Example usage of BattLabOne class"""
    ports = BattLabOne.find_ports()
    if not ports:
        sys.stderr.write("no BattLab-One units detected\n")
        sys.exit(1)

    bl1 = BattLabOne(ports[0])
    bl1.reset()

    print("fw version: {}".format(bl1.version))
    print(bl1.VOLTAGES)

    bl1.current_range = BattLabOne.CurrentRange.HIGH

    bl1.voltage = 3.0

    data = bl1.take_n(bl1.sample(), 100)

    bl1.voltage = 0

    print(max(data), min(data), sum(data) / len(data))


if __name__ == "__main__":
    main()
