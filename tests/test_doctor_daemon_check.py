import os

import pytest

from vmware_knight import doctor


@pytest.fixture
def pid_file(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "CONFIG_DIR", tmp_path)
    return tmp_path / "daemon.pid"


def _no_kill(*args, **kwargs):
    raise AssertionError("os.kill must not be called on Windows: it terminates the process")


def test_no_pid_file_is_ok(pid_file):
    ok, msg = doctor._check_daemon()
    assert ok and "not running" in msg


@pytest.mark.parametrize("alive", [True, False])
def test_windows_never_calls_os_kill(pid_file, monkeypatch, alive):
    pid_file.write_text("4242", encoding="utf-8")
    monkeypatch.setattr(doctor, "_IS_WINDOWS", True)
    monkeypatch.setattr(doctor.os, "kill", _no_kill)
    seen = []
    monkeypatch.setattr(doctor, "_windows_pid_alive", lambda pid: seen.append(pid) or alive)

    ok, msg = doctor._check_daemon()

    assert seen == [4242]
    assert ok is alive
    assert ("Daemon running (PID: 4242)" in msg) if alive else ("stale PID" in msg)


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal-0 probe")
def test_posix_live_process_is_running(pid_file, monkeypatch):
    monkeypatch.setattr(doctor, "_IS_WINDOWS", False)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")

    ok, msg = doctor._check_daemon()

    assert ok and f"Daemon running (PID: {os.getpid()})" in msg


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal-0 probe")
def test_posix_missing_process_is_stale(pid_file, monkeypatch):
    monkeypatch.setattr(doctor, "_IS_WINDOWS", False)
    monkeypatch.setattr(
        doctor.os, "kill", lambda pid, sig: (_ for _ in ()).throw(ProcessLookupError())
    )
    pid_file.write_text("4242", encoding="utf-8")

    ok, msg = doctor._check_daemon()

    assert not ok and "stale PID" in msg


@pytest.mark.skipif(os.name != "nt", reason="needs the Windows API")
def test_windows_pid_alive_real():
    assert doctor._windows_pid_alive(os.getpid()) is True
