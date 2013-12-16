# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

# Copyright (c) 2012-2013, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

""" Unit tests for the cxmanage_api.tests.Dummy class """

import unittest
from mock import Mock, call
from cxmanage_api.tests import Dummy


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

    def test_undefined(self):
        """ Make sure we can call methods that aren't defined in the dummy """
        parent = DummyParent()
        child = DummyChild()

        self.assertTrue(isinstance(parent.p_undefined(), Mock))
        self.assertTrue(isinstance(child.p_undefined(), Mock))
        self.assertTrue(isinstance(child.c_undefined(), Mock))

    def test_defined(self):
        """ Make sure that defined method calls give us their return values """
        parent = DummyParent()
        child = DummyChild()

        self.assertEqual(parent.p_defined(), "DummyParent.p_defined")
        self.assertEqual(child.p_defined(), "DummyParent.p_defined")
        self.assertEqual(child.c_defined(), "DummyChild.c_defined")

    def test_nonexistent(self):
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
        parent.p_undefined()
        parent.p_defined()

        self.assertEqual(
            parent.method_calls, [call.p_undefined(), call.p_defined()]
        )


class Parent(object):
    """ Parent class that we want to mock """
    def p_undefined(self):
        """ Parent method that we'll leave undefined """
        return "Parent.p_undefined"

    def p_defined(self):
        """ Parent method that we'll define in DummyParent """
        return "Parent.p_defined"


class Child(Parent):
    """ Child class that we want to mock """
    def c_undefined(self):
        """ Child method that we'll leave undefined """
        return "Child.c_undefined"

    def c_defined(self):
        """ Child method that we'll define in DummyChild """
        return "Child.c_defined"


class DummyParent(Dummy):
    """ Dummy of the Parent class """
    dummy_spec = Parent

    @property
    def dp_property(self):
        """ Property defined only in DummyParent """
        return "DummyParent.dp_property"

    def p_defined(self):
        """ Dummy definition of Parent.p_defined """
        return "DummyParent.p_defined"


class DummyChild(DummyParent):
    """ Dummy of the Child class. Inherits from DummyParent. """
    dummy_spec = Child

    def c_defined(self):
        """ Dummy definition of Child.c_defined """
        return "DummyChild.c_defined"
