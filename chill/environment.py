#!/usr/bin/env python3

import os
from pathlib import Path

CHILLOS_HOME = Path.home() / ".chillos"
WORKSPACE = CHILLOS_HOME / "workspace"


def initialize():
    CHILLOS_HOME.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    for directory in (
        "home",
        "etc",
        "var",
        "tmp",
        "packages",
    ):
        (WORKSPACE / directory).mkdir(parents=True, exist_ok=True)

    return WORKSPACE


def status():
    workspace = initialize()

    print("CHILLOS ENVIRONMENT")
    print("=" * 40)
    print(f"Home      : {CHILLOS_HOME}")
    print(f"Workspace : {workspace}")
    print("State     : READY")
