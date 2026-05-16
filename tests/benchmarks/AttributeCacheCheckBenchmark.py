import time


class Bench:
    def __init__(self):
        self.a = 1


obj = Bench()


def bench_hasattr():
    count = 0
    start = time.time()
    for _ in range(10000000):
        if hasattr(obj, "a"):
            count += 1
    end = time.time()
    return end - start


# Warmup
bench_hasattr()

print("hasattr time: %.4fs" % bench_hasattr())
