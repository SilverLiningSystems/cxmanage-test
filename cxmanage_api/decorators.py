# pylint: disable=useless-else-on-loop

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

""" Decorators used in cxmanage_api """

from functools import wraps


def retry(count, allowed_errors=Exception):
    """ Create a decorator that retries a function call up to 'count' times.

    :param count: Max retry count
    :type count: integer
    :param allowed_errors: Types of errors to allow
    :type allowed_errors: Exception or iterable

    :return: Function decorator that retries the wrapped function
    :rtype: function

    """
    try:
        allowed_errors = tuple(allowed_errors)
    except TypeError:
        allowed_errors = (allowed_errors,)

    def decorator(function):
        """ The decorator """
        @wraps(function)
        def wrapper(*args, **kwargs):
            """ The wrapper function """
            for _ in range(count):
                try:
                    return function(*args, **kwargs)
                except tuple(allowed_errors):
                    pass
            else:
                return function(*args, **kwargs)

        return wrapper

    return decorator
