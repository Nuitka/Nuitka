from package1.module1 import module1_f1
from package1.module2 import module2_f1
from package1.subpackage2.submodule21 import submodule21_f1
from package1.subpackage1.submodule11 import submodule11_f2


def main():
  module1_f1('package1.main.py')
  module2_f1('package1.main.py')
  submodule11_f2('package1.main.py')
  submodule21_f1('package1.main.py')
