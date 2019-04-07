import os
import sys
from setuptools import setup, find_packages

# use `python setup.py bdist_nuitka` to use nuitka or use 
# in the setup(..., build_with_nuitka=True, ...)
# and bdist and build will allways use nuitka

setup(
    name='bdist_nuitka_test_2',
    description='nuitka bdist_nuitka test-case compiling interdependent' + 
                ' python packages, and printing a data file',
    author='Some Two',
    author_email='some2@sum.e',
    version="0.1",
    py_modules=[],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    command_options={ 'nuitka' : 
        {'--show-scons': True,
         '--show-progress': None,
         '--file-reference-choice':'original', 
        }
    },
    package_data={'': ['*.txt'] },
    scripts = ["runner"],
    zip_safe=False
)
