class NameManglingTest:
    def test(self):
        (__evil := 2)
        print(_NameManglingTest__evil)


NameManglingTest().test()
