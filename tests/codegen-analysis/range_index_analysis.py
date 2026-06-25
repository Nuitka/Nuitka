from __future__ import print_function


def consume(values):
    total = 0

    for index in range(len(values)):
        total += values[index]

    return total


def consume_with_start(values):
    total = 0

    for index in range(5, len(values) + 5):
        total += values[index - 5]

    return total


def main():
    values = list(range(100))

    print(consume(values))
    print(consume_with_start(values))


main()
