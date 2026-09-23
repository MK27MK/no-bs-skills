import functools
import time


def retry_on_error(attempts):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except OSError:
                    if attempt == attempts - 1:
                        raise
                    time.sleep(2**attempt)
        return wrapper
    return decorate
