# Copyright (C) 2007-20010 Michael Foord
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

import os
import sys
import unittest
this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not this_dir in sys.path:
    # Fix for running tests on the Mac 
    sys.path.insert(0, this_dir)


if 'testextendmock' in sys.modules:
    # Fix for running tests under Wing
    import tests
    import testextendmock
    tests.testextendmock = testextendmock

from testcase import TestCase

import inspect
from mock import Mock, mocksignature


class TestMockSignature(TestCase):

    def testFunction(self):
        def f(a):
            pass
        mock = Mock()
        
        f2  = mocksignature(f, mock)
        self.assertRaises(TypeError, f2)
        mock.return_value = 3
        self.assertEquals(f2('foo'), 3)
        mock.assert_called_with('foo')
    
    
    def testMethod(self):
        class Foo(object):
            def method(self, a, b):
                pass
        
        f = Foo()
        mock = Mock()
        mock.return_value = 3
        f.method = mocksignature(f.method, mock)
        self.assertEquals(f.method('foo', 'bar'), 3)
        mock.assert_called_with('foo', 'bar')


    def testFunctionWithDefaults(self):
        def f(a, b=None):
            pass
        mock = Mock()
        f2  = mocksignature(f, mock)
        f2(3)
        mock.assert_called_with(3, None)
        mock.reset_mock()
        
        f2(1, 7)
        mock.assert_called_with(1, 7)
        mock.reset_mock()
        
        f2(b=1, a=7)
        mock.assert_called_with(7, 1)
        mock.reset_mock()
        
        a = object()
        def f(a=a):
            pass
        f2 = mocksignature(f, mock)
        f2()
        mock.assert_called_with(a)
        
    def testIntrospection(self):
        def f(a, *args, **kwargs):
            pass
        f2 = mocksignature(f, f)
        self.assertEqual(inspect.getargspec(f), inspect.getargspec(f2))
        
        def f(a, b=None, c=3, d=object()):
            pass
        f2 = mocksignature(f, f)
        self.assertEqual(inspect.getargspec(f), inspect.getargspec(f2))
    
    
    def testFunctionWithVarArgsAndKwargs(self):
        def f(a, b=None, *args, **kwargs):
            return (a, b, args, kwargs)
        f2 = mocksignature(f, f)
        self.assertEqual(f2(3, 4, 5, x=6, y=9), (3, 4, (5,), {'x': 6, 'y': 9}))
        self.assertEqual(f2(3, x=6, y=9, b='a'), (3, 'a', (), {'x': 6, 'y': 9}))


class TestMockingMagicMethods(TestCase):
    
    def testRepr(self):
        mock = Mock()
        self.assertEqual(repr(mock), object.__repr__(mock))
        mock.__repr__ = lambda self: 'foo'
        self.assertEqual(repr(mock), 'foo')


    def testStr(self):
        mock = Mock()
        self.assertEqual(str(mock), object.__str__(mock))
        mock.__str__ = lambda self: 'foo'
        self.assertEqual(str(mock), 'foo')
    
    
    def testDictMethods(self):
        mock = Mock()
        
        self.assertRaises(TypeError, lambda: mock['foo'])
        def _del():
            del mock['foo']
        def _set():
            mock['foo'] = 3
        self.assertRaises(TypeError, _del)
        self.assertRaises(TypeError, _set)
        
        _dict = {}
        def getitem(s, name):
            return _dict[name]    
        def setitem(s, name, value):
            _dict[name] = value
        def delitem(s, name):
            del _dict[name]
        
        mock.__setitem__ = setitem
        mock.__getitem__ = getitem
        mock.__delitem__ = delitem
        
        self.assertRaises(KeyError, lambda: mock['foo'])
        mock['foo'] = 'bar'
        self.assertEquals(_dict, {'foo': 'bar'})
        self.assertEquals(mock['foo'], 'bar')
        del mock['foo']
        self.assertEquals(_dict, {})
            
            
    def testNumeric(self):
        original = mock = Mock()
        mock.value = 0
        
        self.assertRaises(TypeError, lambda: mock + 3)
        
        def add(self, other):
            mock.value += other
            return self
        mock.__add__ = add
        self.assertEqual(mock + 3, mock)
        self.assertEqual(mock.value, 3)
        
        del mock.__add__
        def iadd(mock):
            mock += 3
        self.assertRaises(TypeError, iadd, mock)
        mock.__iadd__ = add
        mock += 6
        self.assertEqual(mock, original)
        self.assertEqual(mock.value, 9)
        
        self.assertRaises(TypeError, lambda: 3 + mock)
        mock.__radd__ = add
        self.assertEqual(7 + mock, mock)
        self.assertEqual(mock.value, 16)
    
    
    def testHash(self):
        mock = Mock()
        # test delegation
        self.assertEqual(hash(mock), Mock.__hash__(mock))
        
        def _hash(s):
            return 3
        mock.__hash__ = _hash
        self.assertEqual(hash(mock), 3)
    
    
    def testNonZero(self):
        m = Mock()
        self.assertTrue(bool(m))
        
        nonzero = lambda s: False
        m.__nonzero__ = nonzero
        self.assertFalse(bool(m))
    
        
    def testComparison(self):
        self. assertEqual(Mock() < 3, object() < 3)
        self. assertEqual(Mock() > 3, object() > 3)
        self. assertEqual(Mock() <= 3, object() <= 3)
        self. assertEqual(Mock() >= 3, object() >= 3)
        
        mock = Mock()
        def comp(s, o):
            return True
        mock.__lt__ = mock.__gt__ = mock.__le__ = mock.__ge__ = comp
        self. assertTrue(mock < 3)
        self. assertTrue(mock > 3)
        self. assertTrue(mock <= 3)
        self. assertTrue(mock >= 3)

    
    def testEquality(self):
        mock = Mock()
        self.assertEqual(mock, mock)
        self.assertNotEqual(mock, Mock())
        self.assertNotEqual(mock, 3)
        
        def eq(self, other):
            return other == 3
        mock.__eq__ = eq
        self.assertTrue(mock == 3)
        self.assertFalse(mock == 4)
        
        def ne(self, other):
            return other == 3
        mock.__ne__ = ne
        self.assertTrue(mock != 3)
        self.assertFalse(mock != 4)
    
    
    def testLenContainsIter(self):
        mock = Mock()
        
        self.assertRaises(TypeError, len, mock)
        self.assertRaises(TypeError, iter, mock)
        self.assertRaises(TypeError, lambda: 'foo' in mock)
        
        mock.__len__ = lambda s: 6
        self.assertEqual(len(mock), 6)
        
        mock.__contains__ = lambda s, o: o == 3
        self.assertTrue(3 in mock)
        self.assertFalse(6 in mock)
        
        mock.__iter__ = lambda s: iter('foobarbaz')
        self.assertEqual(list(mock), list('foobarbaz'))
        

if __name__ == '__main__':
    unittest.main()
    
