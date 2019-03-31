from __future__ import absolute_import
import six
import sys

MAXSIZE = sys.maxsize

def test_dispatch_types(value):
    assert isinstance(six.MAXSIZE + 23, six.integer_types)
    assert isinstance(six.u("hi"), six.string_types)
    
    class X(object):
        pass
    
    assert isinstance(X, six.class_types)

    

def test__import_module(name):
    from logging import handlers
    m = six._import_module("logging.handlers")
    assert m is handlers


def test__add_doc(func, doc):
    def f():
        """Icky doc"""
        pass

    six._add_doc(f, """New doc""")
    assert f.__doc__ == "New doc"
