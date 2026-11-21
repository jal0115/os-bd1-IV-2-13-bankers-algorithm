import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = [
    sys.executable, "src/cli.py", "10", "5", "7",
    "--max", "examples/book_max.txt",
    "--allocation", "examples/book_allocation.txt",
]


def test_commands_file_matches_stdin():
    commands = ROOT / "examples/book_commands.txt"

    via_stdin = subprocess.run(
        CLI, cwd=ROOT, input=commands.read_bytes(),
        capture_output=True, check=True,
    )
    via_file = subprocess.run(
        CLI + ["--commands", str(commands)], cwd=ROOT,
        stdin=subprocess.DEVNULL, capture_output=True, check=True,
    )

    assert via_file.stdout == via_stdin.stdout
    statuses = [
        line.split(b":", 1)[0]
        for line in via_file.stdout.splitlines()
        if line.startswith((b"granted:", b"wait:", b"unsafe:"))
    ]
    assert statuses == [b"granted", b"wait", b"unsafe"]


def test_missing_commands_file_returns_error(tmp_path):
    missing = tmp_path / "missing-commands.txt"
    result = subprocess.run(
        CLI + ["--commands", str(missing)], cwd=ROOT,
        stdin=subprocess.DEVNULL, capture_output=True,
    )

    assert result.returncode == 2
    assert b"missing-commands.txt" in result.stdout


def test_redirected_output_preserves_mongolian_text(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "cp1251")

    result = subprocess.run(
        CLI + ["--commands", "examples/book_commands.txt"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )

    output = result.stdout.decode("utf-8")
    assert "Төлөв: SAFE" in output
    assert "P0-ийн хүсэлтийг олговол unsafe болно" in output
