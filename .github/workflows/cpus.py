"""How many CPUs this process may use (piggyvisor#31).

`nproc` and `os.cpu_count()` count the CPUs the process may be scheduled on, not the CPU limit of the container it
runs in. The self-hosted runners are containers limited with a CPU quota (12 CPUs on a 24-core host), so worker
counts based on `nproc` start twice as many processes as the container can run. This reads the cgroup quota too
(v2: cpu.max; v1: cpu.cfs_quota_us / cpu.cfs_period_us) and returns the smaller of the two, at least 1.

Run it to print the number: `python .github/workflows/cpus.py`. PIGGY_CGROUP_ROOT points at another cgroup folder
(for tests).
"""

import math
import os
from pathlib import Path


def _quota(root: Path) -> int | None:
    """The CPU quota of the cgroup in whole CPUs (rounded up), or None when there is none."""
    v2 = root / "cpu.max"
    if v2.is_file():
        quota, _, period = v2.read_text().strip().partition(" ")
        if quota != "max" and period:
            return math.ceil(int(quota) / int(period))
        return None
    quota_file, period_file = root / "cpu" / "cpu.cfs_quota_us", root / "cpu" / "cpu.cfs_period_us"
    if quota_file.is_file() and period_file.is_file():
        quota, period = int(quota_file.read_text()), int(period_file.read_text())
        if quota > 0 and period > 0:
            return math.ceil(quota / period)
    return None


def available_cpus() -> int:
    """The CPUs this process may run on, limited by the container's CPU quota."""
    try:
        scheduled = len(os.sched_getaffinity(0))  # what nproc counts (Linux)
    except AttributeError:
        scheduled = os.cpu_count() or 1
    try:
        quota = _quota(Path(os.environ.get("PIGGY_CGROUP_ROOT", "/sys/fs/cgroup")))
    except (OSError, ValueError):
        quota = None
    return max(1, min(scheduled, quota) if quota else scheduled)


if __name__ == "__main__":
    print(available_cpus())
