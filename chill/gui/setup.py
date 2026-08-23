#!/usr/bin/env python3

import json
import shutil
import subprocess
from pathlib import Path


STATE_FILE = Path.home() / ".chillos_setup.json"


def setup_status():

    proot = shutil.which("proot-distro") is not None
    debian = False

    if proot:
        try:
            result = subprocess.run(
                ["proot-distro", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            text = result.stdout + "\n" + result.stderr

            debian = any(
                "debian" in line.lower()
                for line in text.splitlines()
            )

        except Exception:
            debian = False

    completed = False

    try:
        if STATE_FILE.exists():
            data = json.loads(
                STATE_FILE.read_text()
            )
            completed = bool(
                data.get("completed", False)
            )
    except Exception:
        completed = False

    ready = proot and debian

    return {
        "ready": ready,
        "completed": completed,
        "proot_distro": proot,
        "debian": debian,
        "state_file": str(STATE_FILE),
        "commands": {
            "install_proot":
                "pkg install proot-distro -y",
            "install_debian":
                "proot-distro install debian",
            "verify":
                "proot-distro login debian -- cat /etc/os-release"
        }
    }


def complete_setup():

    status = setup_status()

    if not status["ready"]:
        return {
            "success": False,
            "error":
                "PRoot-Distro and Debian are required first."
        }

    STATE_FILE.write_text(
        json.dumps(
            {
                "completed": True
            },
            indent=2
        )
    )

    return {
        "success": True,
        "completed": True
    }


def reset_setup():

    try:

        if STATE_FILE.exists():
            STATE_FILE.unlink()

        return {
            "success": True,
            "completed": False
        }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc)
        }
