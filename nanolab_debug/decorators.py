# decorators.py
import asyncio
import time
from functools import wraps


def ensure_duration(duration=2):

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()

            elapsed_time = end_time - start_time
            remaining_time = duration - elapsed_time

            if remaining_time > 0:
                await asyncio.sleep(remaining_time)

            return result

        return wrapper

    return decorator


def print_dot(func):

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print('.', end='', flush=True)
        return result

    return wrapper