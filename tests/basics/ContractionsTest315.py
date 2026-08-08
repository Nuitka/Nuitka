print([*i for i in [[1, 2, 3], [4, 5, 6]]])
print({*i for i in [[1, 2, 3], [4, 5, 6]]})
print(list((*i for i in [[1, 2, 3], [4, 5, 6]])))
print({**a for a in [{1: 2}, {3: 4}]})


async def numbers():
    yield [1, 2, 3]
    yield [4, 5, 6]


async def listComp():
    print([*i async for i in numbers()])


async def setComp():
    print({*i async for i in numbers()})


async def genExp():
    async for i in (*i async for i in numbers()):
        print(i)


async def dictComp():
    async def dicts():
        yield {1: 2}
        yield {3: 4}

    for i in {**d async for d in dicts()}.items():
        print(i)


def run_coro(coro):
    while True:
        try:
            coro.send(None)
        except StopIteration:
            break


run_coro(listComp())
run_coro(setComp())
run_coro(genExp())
