# Copyright: (c) 2022, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import inspect
import warnings
import functools


def deprecated(func):
    if isinstance(func, (type(b''), type(u''))):
        reason: str = func

        def decorator(func1):
            t: str = "class" if inspect.isclass(func1) else "function"

            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    f"Call to deprecated {t} {func1.__name__} ({reason}).", category=DeprecationWarning, stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func1(*args, **kwargs)
            return new_func1
        return decorator

    elif inspect.isclass(func) or inspect.isfunction(func):

        @functools.wraps(func)
        def new_func2(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                f"Call to deprecated function {func.__name__}.", category=DeprecationWarning, stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            return func(*args, **kwargs)

        return new_func2()


def replaced(func):
    if isinstance(func, (type(b''), type(u''))):
        replacement: str = func

        def decorator(func1):
            t: str = "class" if inspect.isclass(func1) else "function"

            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    f"Deprecated {t} {func1.__name__} replaced by {replacement}.",
                    category=DeprecationWarning, stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func1(*args, **kwargs)
            return new_func1
        return decorator
    else:
        return deprecated(func)
