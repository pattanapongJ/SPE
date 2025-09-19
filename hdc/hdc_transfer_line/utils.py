import time
import cProfile
import pstats
import io
import sys

def profile_me(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats()
    print(s.getvalue())
    return result

def tracefunc(frame, event, arg):
    if event == "call":
        code = frame.f_code
        func_name = code.co_name
        filename = code.co_filename
        lineno = frame.f_lineno
        frame.f_locals["__start_time__"] = time.time()
        print(f"CALL {func_name} ({filename}:{lineno})")
    elif event == "return":
        code = frame.f_code
        func_name = code.co_name
        elapsed = time.time() - frame.f_locals.get("__start_time__", time.time())
        print(f"RETURN {func_name} took {elapsed:.6f}s")
    return tracefunc

def time_to_float(time_str: str) -> float:
    """
    Convert a time string in format 'HH.MM' into float hours.
    Example: '03.13' -> 3.2167 (3 hours + 13 minutes / 60)
    """
    try:
        hours, minutes = map(int, time_str.split("."))
        return hours + minutes / 60
    except ValueError:
        raise ValueError("Time must be in 'HH.MM' format")

def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        elapsed_ms = (time2 - time1) * 1000.0
        elapsed_sec = elapsed_ms / 1000.0

        if elapsed_sec < 1:
            readable = f"{elapsed_ms:.3f} ms"
        elif elapsed_sec < 60:
            readable = f"{elapsed_sec:.3f} sec"
        else:
            minutes = int(elapsed_sec // 60)
            seconds = elapsed_sec % 60
            readable = f"{minutes} min {seconds:.1f} sec"

        print(f"{f.__name__} function took {readable}")
        return ret
    return wrap

