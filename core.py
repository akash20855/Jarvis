import time
import functools
from datetime import datetime
from brain import Brain
brain = Brain()

def self_healing(retries=3, delay=2, fallback=None, tag="api"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    brain.log_event("ERR", tag, f"{func.__name__} attempt {attempt}/{retries}: {e}")
                    if attempt < retries:
                        time.sleep(delay * (2 ** (attempt - 1)))
            if fallback:
                try:
                    brain.log_event("FIX", tag, f"Activating fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                except Exception as fe:
                    brain.log_event("ERR", tag, f"Fallback failed: {fe}")
            brain.store_fix(tag, func.__name__, "unresolved", str(last_error))
            raise last_error
        return wrapper
    return decorator
