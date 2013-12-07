import unittest
from mock import Mock, call
from cxmanage_api.dummy import Dummy


class DummyTest(unittest.TestCase):
    """ Unit tests for the Dummy class.

    These tests are a little unusual since we're not going for code coverage.
    We get 100% code coverage just by calling Dummy().

    Instead, the goal here is to assert that the resulting Dummy object behaves
    in a desirable way. Need to make sure it can be subclassed properly,
    passes the isinstance test, method calls are tracked properly, etc.

    """

    def test_isinstance(self):
        """ Make sure dummy classes, with specs, pass the isinstance test """
        self.assertTrue(isinstance(DummyParent(), Parent))
        self.assertTrue(isinstance(DummyChild(), Parent))
        self.assertTrue(isinstance(DummyChild(), Child))

    def test_ignored(self):
        """ Make sure we can call methods that aren't defined in the dummy """
        parent = DummyParent()
        child = DummyChild()

        self.assertTrue(isinstance(parent.p_ignored(), Mock))
        self.assertTrue(isinstance(child.p_ignored(), Mock))
        self.assertTrue(isinstance(child.c_ignored(), Mock))

    def test_defined(self):
        """ Make sure that defined method calls give us their return values """
        parent = DummyParent()
        child = DummyChild()

        self.assertEqual(parent.p_defined(), "DummyParent.p_defined")
        self.assertEqual(child.p_defined(), "DummyParent.p_defined")
        self.assertEqual(child.c_defined(), "DummyChild.c_defined")

    def test_undefined(self):
        """ Make sure we raise an error if we call a nonexistent method """
        parent = DummyParent()
        child = DummyChild()

        with self.assertRaises(AttributeError):
            parent.undefined()
        with self.assertRaises(AttributeError):
            child.undefined()

    def test_dummy_property(self):
        """ Test that dummies don't blow up with properties """
        parent = DummyParent()
        child = DummyChild()
        self.assertEqual(parent.dp_property, "DummyParent.dp_property")
        self.assertEqual(child.dp_property, "DummyParent.dp_property")

    def test_method_calls(self):
        """ Test that method calls can be tracked """
        parent = DummyParent()
        parent.p_ignored()
        parent.p_defined()

        self.assertEqual(
            parent.method_calls, [call.p_ignored(), call.p_defined()]
        )


class Parent(object):
    """ Parent class that we want to mock """
    def p_ignored(self):
        return "Parent.p_ignored"

    def p_defined(self):
        return "Parent.p_defined"


class Child(Parent):
    """ Child class that we want to mock """
    def c_ignored(self):
        return "Child.c_ignored"

    def c_defined(self):
        return "Child.c_defined"


class DummyParent(Dummy):
    """ Dummy of the Parent class """
    dummy_spec = Parent

    @property
    def dp_property(self):
        return "DummyParent.dp_property"

    def p_defined(self):
        return "DummyParent.p_defined"


class DummyChild(DummyParent):
    """ Dummy of the Child class. Inherits from DummyParent. """
    dummy_spec = Child

    def c_defined(self):
        return "DummyChild.c_defined"
