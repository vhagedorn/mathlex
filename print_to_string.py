import sys
import io
from contextlib import contextmanager

@contextmanager
def print_to_string():
    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer
    try:
        yield buffer
    finally:
        sys.stdout = old_stdout
