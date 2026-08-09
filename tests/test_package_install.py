import json
import os
import subprocess
import sys
from pathlib import Path


def test_noneditable_install_exposes_python_module_runtime(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    target = tmp_path / "installed"
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--target",
            str(target),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stdout + "\n" + install.stderr

    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    completed = subprocess.run(
        [sys.executable, "-m", "rakl", "profiles"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert any(profile["profile_id"] == "ordinary-8k" for profile in payload["profiles"])
