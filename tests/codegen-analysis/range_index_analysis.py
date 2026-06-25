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


def assign_with_start(values):
    for index in range(3, len(values) + 3):
        values[index - 3] = index

    return values


def inplace_with_start(values):
    total = 0

    for index in range(10, len(values) + 10):
        offset = index - 10
        offset += index
        offset -= index
        total += values[offset]

    return total


def object_result_with_start(values):
    result = []

    for index in range(1, len(values) + 1):
        result.append(index + 1)

    return result


def comparison_with_start(values):
    result = 0
    limit = len(values)

    for index in range(1, limit + 1):
        if index + 1 > limit:
            result += index

    return result


def modulo_with_start(values):
    result = 0

    for index in range(2, len(values) + 2):
        result += index % 2

    return result


def inplace_modulo_with_start(values):
    result = 0

    for index in range(2, len(values) + 2):
        offset = index
        offset %= 2
        result += offset

    return result


def while_increment(values):
    index = 0
    limit = len(values)

    while index < limit:
        index += 1

    return index


def compare_large_limit():
    index = 1
    limit = 10**100

    return index < limit, limit > index, index == limit, index != limit


def floordiv_with_start(values):
    result = 0

    for index in range(2, len(values) + 2):
        result += index // 2

    return result


def main():
    values = list(range(100))

    print(consume(values))
    print(consume_with_start(values))
    print(assign_with_start([0, 0, 0, 0, 0]))
    print(inplace_with_start(values))
    print(object_result_with_start([0, 0, 0]))
    print(comparison_with_start([0, 0, 0]))
    print(floordiv_with_start([0, 0, 0]))
    print(modulo_with_start([0, 0, 0]))
    print(inplace_modulo_with_start([0, 0, 0]))
    print(while_increment([0, 0, 0]))
    print(compare_large_limit())


main()
