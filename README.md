# README

The battlab module provides a Python 3 class for interacting with a [BattLab-One instrument](https://bluebird-labs.com/).

* Encapsulates serial protocol with device firmware
* Configure operating parameters
* Read samples of current readings
* Usable from CLI and GUI applications
* Cross-platform

Use help(BattLabOne) for docs.

A command-line utility is provided in `bl1cli.py`. Invoke using `python3 -m battlab` or `bl1cli` after installing via `setup.py` or `pip3 install`.

## Examples

From `examples/basic/main.py`:

``` python
from battlab import BattLabOne

def main():
    """Example usage of BattLabOne class"""
    bl1 = BattLabOne()
    bl1.reset()

    print("fw version: {}".format(bl1.version))
    print(bl1.VOLTAGES)

    bl1.current_range = BattLabOne.CurrentRange.HIGH

    bl1.voltage = 3.0

    data = bl1.sample_block(1.5)

    bl1.voltage = 0

    print(max(data), min(data), sum(data) / len(data))


if __name__ == "__main__":
    main()

```

See `examples/gui` for an example that uses [PySimpleGUI](https://pysimplegui.readthedocs.io/en/latest) and [matplotlib](https://matplotlib.org) for a simple GUI application including plotting.
