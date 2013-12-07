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

from mock import Mock
from types import MethodType


class Dummy(object):
    """ Dummy class. Instantiating this actually gives us a Mock object, so we
    can make assertions about method calls and their ordering

    They dummy_spec variable gives us a spec for building the Mock object, which
    restricts the names of methods that can be called.

    """

    dummy_spec = None

    def __new__(cls, *args, **kwargs):
        self = super(Dummy, cls).__new__(cls, *args, **kwargs)
        self.__init__(*args, **kwargs)

        mock = Mock(spec=cls.dummy_spec, name=cls.__name__)

        # Manually add our side effects and attributes to the mock
        for name, value in vars(cls).items():
            try:
                # Try adding it as a method
                getattr(mock, name).side_effect = MethodType(
                    value, mock, cls
                )
            except (AttributeError, TypeError):
                try:
                    # Not callable, so set it as a class variable instead
                    setattr(mock, name, value)
                except (AttributeError, TypeError):
                    pass

        # Now add any instance variables that were created in self.__init__
        for name, value in vars(self).items():
            setattr(mock, name, value)

        return mock
