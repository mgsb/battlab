from battlab import BattLabOne


def main():
    """Example usage of BattLabOne class with triggered sampling"""
    bl1 = BattLabOne()
    bl1.reset()

    bl1.current_range = BattLabOne.CurrentRange.HIGH

    bl1.voltage = 3.7

    samples = bl1.sample(True)
    for cnt, data in enumerate(samples):
        if data > 0.0:
            break
        if cnt % 1000 == 0:
            print("waiting for trigger: ", cnt, end="\r")

    print("\ntriggered - acquiring samples")
    data = bl1.take_n(samples, 10000)

    bl1.voltage = 0

    print(len(data), max(data), min(data), sum(data) / len(data))


if __name__ == "__main__":
    main()
