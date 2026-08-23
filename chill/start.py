#!/usr/bin/env python3

import os
import subprocess

from .environment import initialize


def main():
    workspace = initialize()

    print()
    print("Starting ChillOS...")
    print(f"Workspace: {workspace}")
    print()

    env = os.environ.copy()
    env["CHILLOS_HOME"] = str(workspace)
    env["CHILLOS_ACTIVE"] = "1"

    shell = os.environ.get("SHELL", "/system/bin/sh")

    subprocess.run(
        [shell],
        cwd=str(workspace),
        env=env,
    )

    print()
    print("ChillOS session ended.")


if __name__ == "__main__":
    main()
