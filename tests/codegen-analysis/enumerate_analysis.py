from __future__ import print_function


def consume(values):
    total = 0

    for index, value in enumerate(values):
        total += index + value

    return total


def consume_with_start(values):
    total = 0

    for index, value in enumerate(values, 5):
        total += index + value

    return total


def consume_next(values):
    iterator = enumerate(values)

    return next(iterator)


def main():
    values = list(range(100))

    print(consume(values))
    print(consume_with_start(values))
    print(consume_next("abc"))


main()
