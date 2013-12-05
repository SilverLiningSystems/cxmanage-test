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

from mock import Mock, PropertyMock


def Dummy(spec):
    """ Returns a dummy that behaves like the specified class.

    The returned value is a Class, not an Instance, so it can be subclassed.

    By default, any attribute accessed in an instance will be equal to None.
    Return values, or other side effects, can be defined by overriding the
    functions/properties in a subclass.

    """
    class SpeccedDummy(object):
        """ Specced dummy class. Instantiating this actually gives us a Mock
        object, defined by spec, that wraps ourselves.

        """
        def __new__(cls, *args, **kwargs):
            self = super(SpeccedDummy, cls).__new__(cls, *args, **kwargs)
            self.__init__(*args, **kwargs)
            variables = vars(self)
            self = Mock(spec=spec, wraps=self, name=cls.__name__)
            for name, value in variables.items():
                setattr(self, name, value)
            return self

        def __getattr__(self, name):
            """ Return None for any undefined attributes.

            This is necessary to allow for attributes that are found in the
            spec, but not defined in any subclass of SpeccedDummy.

            """
            return None

    return SpeccedDummy
