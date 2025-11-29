from contextlib import contextmanager
import time


@contextmanager
def timer(description: str = "Operation"):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"⏱️ {description}: {end - start:.4f}s")
