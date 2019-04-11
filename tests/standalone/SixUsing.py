import six
import sys
import unittest


def dispatch_types(value):
   
    if isinstance(value, six.integer_types):
        return int

    elif isinstance(value, six.string_types):
        return str
    
    elif isinstance(value, six.binary_type):
        return bytes

def get_iterator(dictionary):
    return six.viewkeys(dictionary), six.viewvalues(dictionary), six.viewitems(dictionary)


class TestAssertCountEqual(unittest.TestCase):
    def test(self):
        six.assertCountEqual(self, (1, 2), [2, 1])
        

def main():
    print(dispatch_types(6))
    print(dispatch_types('hi'))
    u='hi'
    print(dispatch_types(u.encode('utf-8')))
    Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25} 
    print(get_iterator(Dict))
    
    t=TestAssertCountEqual()
    print(t.test)
   

if __name__ == "__main__":
    main()


