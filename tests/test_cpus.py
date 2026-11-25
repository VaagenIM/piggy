"""The CPU count for the Pages build follows the container's CPU limit, not the host's cores (piggyvisor#31)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "workflows"))

from cpus import available_cpus  # noqa: E402

SCHEDULED = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)


def test_a_cgroup_v2_quota_limits_the_count(tmp_path, monkeypatch):
    monkeypatch.setenv("PIGGY_CGROUP_ROOT", str(tmp_path))
    (tmp_path / "cpu.max").write_text("100000 100000\n")
    assert available_cpus() == 1
    (tmp_path / "cpu.max").write_text("max 100000\n")
    assert available_cpus() == SCHEDULED


def test_a_cgroup_v1_quota_is_rounded_up(tmp_path, monkeypatch):
    monkeypatch.setenv("PIGGY_CGROUP_ROOT", str(tmp_path))
    (tmp_path / "cpu").mkdir()
    (tmp_path / "cpu" / "cpu.cfs_quota_us").write_text("150000\n")
    (tmp_path / "cpu" / "cpu.cfs_period_us").write_text("100000\n")
    assert available_cpus() == min(2, SCHEDULED)
    (tmp_path / "cpu" / "cpu.cfs_quota_us").write_text("-1\n")
    assert available_cpus() == SCHEDULED


def test_without_a_cgroup_the_scheduled_cpus_count(tmp_path, monkeypatch):
    monkeypatch.setenv("PIGGY_CGROUP_ROOT", str(tmp_path / "missing"))
    assert available_cpus() == SCHEDULED
