import time
from time import process_time

if hasattr('time', 'process_time_ns'):
    from time import process_time_ns
else:
    def process_time_ns() -> int:
        return int(process_time() * 1e9)

# time.get_clock_info('process_time')
# - monotonic, not adjustable clock
# - 0.1 microsecond resolution
# time.get_clock_info('time')
# - adjustable clock which may include leap seconds,
#   we cannot use it to measure CPU time
# - 15 ms of resolution (Windows)

reference_point: int = process_time_ns()


def reset_countdown_timer():
    """
    Useful in our testing scripts.
    """
    global reference_point
    reference_point = process_time_ns()


last_tic: int = reference_point + 0


def tic():
    global last_tic
    last_tic = process_time_ns()


def tac_ns() -> int:
    return process_time_ns() - last_tic


def tac() -> float:
    return tac_ns() * 1e-9  # int to float, precision loss


def get_cpu_time_ns() -> int:
    """
    Returns nanoseconds.
    """
    return process_time_ns() - reference_point


def get_cpu_time_left_ns() -> int:
    """
    Return time remaining to 5 minutes in nanoseconds
    """
    return 300_000_000_000 - get_cpu_time_ns()


def get_cpu_time_left() -> float:
    """
    Return time remaining to 5 minutes. (in seconds)

    This value will be checked by solvers
    to adjust to the 5-minute limit.
    """
    return 300 - (1e-9 * get_cpu_time_ns())
